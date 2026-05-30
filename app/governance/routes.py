from flask import Blueprint, session, jsonify
import github
from github import Github
from ..workspace.utils import mask_token
from ..repos.routes import fetch_security_info

bp = Blueprint('governance', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(auth=github.Auth.Token(token), timeout=30)

def evaluate_repo_policy(repo):
    """
    Evaluates repository compliance against standard governance rules.
    Returns: (compliant, violations, policies)
    """
    # Default Policies (MVP)
    policies = {
        "block_merge_on_critical_security": True,
        "block_merge_on_failing_ci": True
    }

    violations = []

    # 1. Evaluate Security Policy
    sec_summary, _ = fetch_security_info(repo)
    if policies["block_merge_on_critical_security"]:
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

    return len(violations) == 0, violations, policies

@bp.route('/api/repos/<path:full_name>/governance/policy', methods=['GET'])
def get_repo_governance(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        compliant, violations, policies = evaluate_repo_policy(repo)

        return jsonify({
            "repo": full_name,
            "policies": policies,
            "compliant": compliant,
            "violations": violations
        }), 200

    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
