import os
import shutil
import git
import datetime
import tempfile
from flask import Blueprint, request, session, jsonify
import github
from github import Github
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from ..workspace.utils import render_template_dir, mask_token, get_templates_root

bp = Blueprint('repos', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    # Security Enhancement: Add timeout to prevent resource exhaustion from hanging API calls
    return Github(auth=github.Auth.Token(token), timeout=30)

@bp.route('/api/user/orgs', methods=['GET'])
def list_orgs():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Cache organizations in session to optimize performance and prevent rate limiting
        if 'user_orgs' in session:
            return jsonify(session['user_orgs']), 200

        user = g.get_user()
        orgs = user.get_orgs()
        results = []
        for org in orgs:
            results.append({
                "login": org.login,
                "avatar_url": org.avatar_url
            })

        session['user_orgs'] = results
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/user/orgs/<org_name>/teams', methods=['GET'])
def list_teams(org_name):
    # Security Enhancement: Input validation for org_name
    if org_name and len(org_name) > 100:
        return jsonify({"error": "org_name is too long"}), 400

    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user = g.get_user()
        teams = user.get_teams()
        results = []
        for team in teams:
            if team.organization.login.lower() == org_name.lower():
                results.append({
                    "id": team.id,
                    "name": team.name,
                    "slug": team.slug
                })

        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos', methods=['GET'])
def list_repos():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    search_query = request.args.get('search')
    org_name = request.args.get('org_name')
    team_id = request.args.get('team_id')

    # Security Enhancement: Input validation and length limits
    if search_query and len(search_query) > 200:
        return jsonify({"error": "search query is too long"}), 400
    if org_name and len(org_name) > 100:
        return jsonify({"error": "org_name is too long"}), 400
    if team_id:
        try:
            team_id = int(team_id)
        except ValueError:
            return jsonify({"error": "Invalid team_id"}), 400

    try:
        user = g.get_user()

        # Determine context: specific organization or current user
        context_login = org_name if org_name else user.login
        is_org = bool(org_name)

        if team_id:
            # List repos for a specific team
            org = g.get_organization(org_name) if org_name else user.get_orgs()[0] # Fallback if org_name missing
            repos = org.get_team(int(team_id)).get_repos(sort='pushed', direction='desc')
        elif search_query:
            # Filtered search within chosen context
            query = f"org:{org_name} {search_query}" if is_org else f"user:{user.login} {search_query}"
            repos = g.search_repositories(query)
        elif is_org:
            # List repos for organization
            repos = g.get_organization(org_name).get_repos(sort='pushed', direction='desc')
        else:
            # Default to user's repos, recently pushed
            repos = user.get_repos(sort='pushed', direction='desc')

        results = []
        # Pre-fetch Issue and PR counts using Search API to avoid N+1 problem
        # Scalability: Capped at top 100 most recently updated to prevent timeouts in large orgs
        pr_counts = {}
        issue_counts = {}
        try:
            if team_id:
                # If team_id is active, we ideally want to scope search to team repos.
                # However, GitHub search 'team:' filter is for team reviewers/mentions,
                # not for repos associated with a team.
                # We'll use the repository list we just fetched to filter the search if needed,
                # or just use the org context as a fallback.
                search_context = f"org:{org_name}" if is_org else f"user:{user.login}"
            else:
                search_context = f"org:{org_name}" if is_org else f"user:{user.login}"

            open_prs = g.search_issues(f"is:pr is:open {search_context}")
            for i, pr in enumerate(open_prs):
                if i >= 100: break
                repo_full_name = pr.repository.full_name
                pr_counts[repo_full_name] = pr_counts.get(repo_full_name, 0) + 1

            open_issues = g.search_issues(f"is:issue is:open {search_context}")
            for i, issue in enumerate(open_issues):
                if i >= 100: break
                repo_full_name = issue.repository.full_name
                issue_counts[repo_full_name] = issue_counts.get(repo_full_name, 0) + 1
        except Exception:
            # Fallback to 0 if search fails
            pass

        for i, repo in enumerate(repos):
            if i >= 30: break
            results.append({
                "full_name": str(repo.full_name),
                "name": str(repo.name),
                "description": str(repo.description) if repo.description else "",
                "html_url": str(repo.html_url),
                "stargazers_count": int(repo.stargazers_count) if repo.stargazers_count is not None else 0,
                "open_issues_count": int(issue_counts.get(repo.full_name, 0)),
                "open_prs_count": int(pr_counts.get(repo.full_name, 0)),
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "private": bool(repo.private)
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos', methods=['POST'])
@bp.route('/api/repos/create', methods=['POST'])
def create_repo():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or request.form
    name = data.get('name')
    description = data.get('description', '')
    visibility = data.get('visibility', 'public')
    private = visibility == 'private'

    if not name:
        return jsonify({"error": "Repository name is required"}), 400

    # Security Enhancement: Input length validation
    if len(name) > 100:
        return jsonify({"error": "Repository name is too long (max 100 characters)"}), 400
    if description and len(description) > 1024:
        return jsonify({"error": "Description is too long (max 1024 characters)"}), 400

    if not secure_filename(name):
        return jsonify({"error": "Invalid repository name"}), 400

    template_name = data.get('template_name')
    context = data.get('context', {})
    if isinstance(context, str):
        try:
            import json
            context = json.loads(context)
        except Exception:
            context = {}

    if template_name:
        template_name = secure_filename(template_name)
        if not template_name:
            return jsonify({"error": "Invalid template name"}), 400

    try:
        user = g.get_user()
        repo = user.create_repo(
            name,
            description=description,
            private=private
        )

        if template_name:
            templates_root = get_templates_root()
            template_path = os.path.join(templates_root, template_name)

            if os.path.exists(template_path):
                # Temporary directory for cloning and initializing
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Clone the new repository
                    auth_url = repo.clone_url.replace('https://github.com/', f'https://{session["github_token"]}@github.com/')
                    local_repo = git.Repo.clone_from(auth_url, tmp_dir)

                    # Use render_template_dir for dynamic scaffolding
                    render_template_dir(template_path, tmp_dir, context)

                    # Configure Git identity
                    with local_repo.config_writer() as cw:
                        cw.set_value("user", "name", "GH-Web User")
                        cw.set_value("user", "email", "gh-web@example.com")

                    # Commit and push
                    local_repo.git.add(A=True)
                    local_repo.index.commit("Initial commit from template")
                    local_repo.git.push('origin', 'main')

        return jsonify({
            "message": f"Repository {name} created successfully" + (" with template" if template_name else ""),
            "full_name": repo.full_name,
            "clone_url": repo.clone_url
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

def fetch_security_info(repo):
    summary = {
        "vulnerabilities": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        "secrets": {"open": 0},
        "code_scanning": {"errors": 0, "warnings": 0}
    }
    alerts = []

    # 1. Dependabot Alerts
    try:
        dep_alerts = repo.get_dependabot_alerts(state='open')
        for alert in dep_alerts:
            severity = str(alert.security_advisory.severity).lower()
            if severity in summary["vulnerabilities"]:
                summary["vulnerabilities"][severity] += 1

            alerts.append({
                "type": "dependabot",
                "number": int(alert.number),
                "severity": severity,
                "package": str(alert.security_vulnerability.package.name),
                "fixed_in": str(alert.security_vulnerability.first_patched_version_identifier) if alert.security_vulnerability.first_patched_version_identifier else None,
                "html_url": str(alert.html_url),
                "created_at": alert.created_at.isoformat() if alert.created_at else None
            })
    except Exception:
        pass

    # 2. Secret Scanning Alerts
    try:
        secret_alerts = repo.get_secret_scanning_alerts(state='open')
        for alert in secret_alerts:
            summary["secrets"]["open"] += 1
            alerts.append({
                "type": "secret",
                "secret_type": str(alert.secret_type),
                "html_url": str(alert.html_url)
            })
    except Exception:
        pass

    # 3. Code Scanning Alerts
    try:
        code_alerts = repo.get_codescan_alerts(state='open')
        for alert in code_alerts:
            severity = str(alert.rule.severity).lower()
            if severity == 'error':
                summary["code_scanning"]["errors"] += 1
            elif severity in ['warning', 'note']:
                summary["code_scanning"]["warnings"] += 1

            alerts.append({
                "type": "code_scanning",
                "severity": severity,
                "rule": str(alert.rule.description),
                "html_url": str(alert.html_url)
            })
    except Exception:
        pass

    return summary, alerts

@bp.route('/api/repos/<path:full_name>/security/alerts', methods=['GET'])
def get_security_alerts(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        summary, alerts = fetch_security_info(repo)
        return jsonify({
            "summary": summary,
            "alerts": alerts
        }), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/health', methods=['GET'])
def get_repos_health():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    repo_names = request.args.get('repos', '').split(',')
    repo_names = [r.strip() for r in repo_names if r.strip()]

    if not repo_names:
        return jsonify({}), 200

    # Security Enhancement: Limit the number of repositories to process and validate name lengths
    if len(repo_names) > 50:
        return jsonify({"error": "Too many repositories requested (max 50)"}), 400

    for name in repo_names:
        if len(name) > 255:
            return jsonify({"error": f"Repository name too long: {name[:50]}..."}), 400

    def fetch_repo_health(full_name):
        try:
            repo = g.get_repo(full_name)
            health = {
                "full_name": full_name,
                "ci_status": None,
                "production_status": None,
                "security_status": "success",
                "security_summary": None
            }

            # 0. Security Status
            try:
                sec_summary, _ = fetch_security_info(repo)
                health["security_summary"] = sec_summary

                # Scoring Logic: failure for critical/high vulnerabilities or open secrets
                if (sec_summary["vulnerabilities"]["critical"] > 0 or
                    sec_summary["vulnerabilities"]["high"] > 0 or
                    sec_summary["secrets"]["open"] > 0):
                    health["security_status"] = "failure"
                elif (sec_summary["vulnerabilities"]["medium"] > 0 or
                      sec_summary["vulnerabilities"]["low"] > 0 or
                      sec_summary["code_scanning"]["errors"] > 0 or
                      sec_summary["code_scanning"]["warnings"] > 0):
                    health["security_status"] = "warning"
            except:
                pass

            # 1. CI Status for default branch
            try:
                # get_combined_status takes a ref
                combined = repo.get_combined_status(repo.default_branch)
                health["ci_status"] = str(combined.state)
            except:
                pass

            # 2. Next Milestone
            try:
                milestones = repo.get_milestones(state='open', sort='due_on', direction='asc')
                for ms in milestones:
                    if ms.due_on:
                        health["next_milestone"] = {
                            "title": str(ms.title),
                            "due_on": ms.due_on.isoformat(),
                            "overdue": ms.due_on < datetime.datetime.now(ms.due_on.tzinfo) if ms.due_on.tzinfo else ms.due_on < datetime.datetime.now()
                        }
                        break
            except:
                pass

            # 3. Production Status
            try:
                # Try to find 'production' environment robustly
                envs = repo.get_environments()
                prod_env = None
                # Check for common production synonyms
                synonyms = ['production', 'prod', 'live']
                for env in envs:
                    if env.name.lower() in synonyms:
                        prod_env = env
                        break

                # Fallback to the first environment if no explicit 'production' is found
                if not prod_env:
                    for env in envs:
                        prod_env = env
                        break

                if prod_env:
                    deployments = repo.get_deployments(environment=prod_env.name)
                    for d in deployments:
                        # Get latest status
                        statuses = d.get_statuses()
                        latest = None
                        for s in statuses:
                            latest = s
                            break

                        health["production_status"] = {
                            "env": prod_env.name,
                            "state": latest.state if latest else "unknown",
                            "ref": d.ref
                        }
                        break # Only need the latest deployment
            except:
                pass

            return health
        except Exception:
            return {"full_name": full_name, "error": "Not Found"}

    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_repo_health, name) for name in repo_names]
        for future in futures:
            res = future.result()
            results[res["full_name"]] = res

    return jsonify(results), 200
