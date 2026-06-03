from flask import Blueprint, session, jsonify, request
import github
import datetime
from concurrent.futures import ThreadPoolExecutor
from github import Github
from ..workspace.utils import mask_token
from ..repos.routes import fetch_security_info
from ..pulse.routes import calculate_repo_pulse
from .policy_store import PolicyStore

bp = Blueprint('governance', __name__)
policy_store = PolicyStore()

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(auth=github.Auth.Token(token), timeout=30)

def evaluate_repo_policy(repo):
    """
    Evaluates repository compliance against standard governance rules.
    Returns: (compliant, violations, policies, sources)
    """
    policies, sources = policy_store.get_effective_policy_with_sources(repo.full_name)

    violations = []

    # 1. Evaluate Security Policy
    sec_summary, alerts = fetch_security_info(repo)
    if policies.get("block_merge_on_critical_security"):
        if sec_summary["vulnerabilities"]["critical"] > 0:
            violations.append({
                "policy": "block_merge_on_critical_security",
                "message": f"Critical vulnerabilities detected: {sec_summary['vulnerabilities']['critical']}",
                "severity": "high"
            })
        if sec_summary["secrets"]["open"] > 0:
            violations.append({
                "policy": "block_merge_on_critical_security",
                "message": f"Open secrets detected: {sec_summary['secrets']['open']}",
                "severity": "high"
            })

    # 1b. SLA Compliance Check
    sla_hours = policies.get("sla_critical_hours", 48)
    sla_violated = False
    now = datetime.datetime.now(datetime.timezone.utc)

    for alert in alerts:
        if alert.get("type") == "dependabot" and alert.get("severity") == "critical":
            created_at_str = alert.get("created_at")
            if created_at_str:
                created_at = datetime.datetime.fromisoformat(created_at_str)
                age = now - created_at
                if age.total_seconds() / 3600 > sla_hours:
                    sla_violated = True
                    break

    if sla_violated:
        policies["sla_violation"] = True
        if policies.get("block_merge_on_sla_violation"):
            violations.append({
                "policy": "block_merge_on_sla_violation",
                "message": f"SLA Violation: Critical vulnerability older than {sla_hours}h",
                "severity": "high"
            })
    else:
        policies["sla_violation"] = False

    # 2. Evaluate CI Policy
    if policies["block_merge_on_failing_ci"]:
        try:
            combined = repo.get_combined_status(repo.default_branch)
            if combined.state == 'failure':
                violations.append({
                    "policy": "block_merge_on_failing_ci",
                    "message": "CI status is failing on default branch",
                    "severity": "high"
                })
        except:
            pass

    return len(violations) == 0, violations, policies, sources

@bp.route('/api/repos/<path:full_name>/governance/policy', methods=['GET'])
def get_repo_governance(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        compliant, violations, policies, sources = evaluate_repo_policy(repo)

        return jsonify({
            "repo": full_name,
            "policies": policies,
            "sources": sources,
            "compliant": compliant,
            "violations": violations
        }), 200

    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/governance/orgs/<path:org_name>/policy', methods=['GET'])
def get_org_governance(org_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Check if org exists
        g.get_organization(org_name)
        policy, sources = policy_store.get_org_policy_with_sources(org_name)

        return jsonify({
            "org": org_name,
            "policies": policy,
            "sources": sources
        }), 200

    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/governance/orgs/<path:org_name>/policy', methods=['PATCH'])
def update_org_governance(org_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Verify user is an admin or has sufficient permissions in the org
        org = g.get_organization(org_name)
        user = g.get_user()

        # Simple permission check: must be a member, and we'll check if they can push to a repo in the org as a proxy for 'maintainer'
        # Ideally we check org membership role, but that requires specific scopes.
        # For Phase 5, we'll check if they are a member.
        try:
            membership = org.get_membership(user.login)
            if membership.role not in ['admin', 'maintainer']:
                 return jsonify({"error": f"Forbidden: {membership.role} role does not have permission to update organization policy"}), 403
        except:
            return jsonify({"error": "Forbidden: Organization access required"}), 403

        data = request.get_json(silent=True) or request.form
        if not data:
            return jsonify({"error": "No data provided"}), 400

        try:
            updated_policy = policy_store.update_org_policy(org_name, data)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400

        return jsonify({
            "message": f"Policy for {org_name} updated successfully",
            "policies": updated_policy
        }), 200

    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/portfolio/governance/heatmap', methods=['GET'])
def get_portfolio_heatmap():
    token = session.get('github_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    repo_names = request.args.get('repos', '').split(',')
    repo_names = [r.strip() for r in repo_names if r.strip()]

    if not repo_names:
        return jsonify([]), 200

    if len(repo_names) > 50:
        return jsonify({"error": "Too many repositories (max 50)"}), 400

    g = get_github_client()

    def fetch_repo_heatmap_data(full_name):
        try:
            repo = g.get_repo(full_name)
            pulse = calculate_repo_pulse(g, full_name)
            compliant, violations, policies, sources = evaluate_repo_policy(repo)

            freshness = pulse.get("metrics", {}).get("dependency_freshness_index", 0) or 0
            mttr = pulse.get("metrics", {}).get("security_mttr_hours", 0) or 0

            # Quadrant Mapping
            # X-Axis: Freshness (0-100), Y-Axis: MTTR (Inverted scale 0-100 where 0 is high MTTR)
            # Thresholds: Freshness 80%, MTTR 24h
            FRESHNESS_THRESHOLD = 80
            MTTR_THRESHOLD = 24

            quadrant = "Elite" # Default
            if freshness >= FRESHNESS_THRESHOLD and mttr <= MTTR_THRESHOLD:
                quadrant = "Elite"
            elif freshness < FRESHNESS_THRESHOLD and mttr <= MTTR_THRESHOLD:
                quadrant = "Artisans"
            elif freshness < FRESHNESS_THRESHOLD and mttr > MTTR_THRESHOLD:
                quadrant = "Critical Debt"
            else:
                quadrant = "Fragile Elite"

            return {
                "repo": full_name,
                "x": freshness,
                "y": mttr,
                "quadrant": quadrant,
                "compliant": compliant,
                "sla_violation": policies.get("sla_violation", False)
            }
        except:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_repo_heatmap_data, name) for name in repo_names]
        for future in futures:
            res = future.result()
            if res:
                results.append(res)

    return jsonify(results), 200

@bp.route('/api/repos/<path:full_name>/governance/policy', methods=['PATCH'])
def update_repo_governance(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Verify user has push access to update policy
        repo = g.get_repo(full_name)
        if not repo.permissions.push:
            return jsonify({"error": "Forbidden: Push access required to update policy"}), 403

        data = request.get_json(silent=True) or request.form
        if not data:
            return jsonify({"error": "No data provided"}), 400

        try:
            updated_policy = policy_store.update_repo_policy(full_name, data)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400

        return jsonify({
            "message": f"Policy for {full_name} updated successfully",
            "policies": updated_policy
        }), 200

    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
