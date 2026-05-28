import os
from flask import Blueprint, request, session, jsonify
import github
from github import Github
import git
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from ..workspace.utils import mask_token, get_repo_full_name_from_url

bp = Blueprint('milestones', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    # Security Enhancement: Add timeout to prevent resource exhaustion from hanging API calls
    return Github(auth=github.Auth.Token(token), timeout=30)

@bp.route('/api/repos/<path:full_name>/milestones', methods=['GET'])
def list_milestones(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    state = request.args.get('state', 'open')

    # Security Enhancement: Whitelist state parameter
    if state not in ['open', 'closed', 'all']:
        return jsonify({"error": "Invalid state parameter"}), 400

    try:
        repo = g.get_repo(full_name)
        milestones = repo.get_milestones(state=state)
        # Security Enhancement: Limit to first 100 items to prevent DoS/resource exhaustion
        results = []
        for i, ms in enumerate(milestones):
            if i >= 100: break
            results.append({
                "number": int(ms.number),
                "title": str(ms.title),
                "description": str(ms.description) if ms.description else "",
                "state": str(ms.state),
                "open_issues": int(ms.open_issues),
                "closed_issues": int(ms.closed_issues),
                "due_on": ms.due_on.isoformat() if ms.due_on else None,
                "html_url": str(ms.html_url)
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/milestones', methods=['POST'])
def create_milestone(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    title = data.get('title')
    description = data.get('description', '')
    due_on = data.get('due_on') # Expected in ISO format if provided

    if not title:
        return jsonify({"error": "Milestone title is required"}), 400

    # Security Enhancement: Input length validation
    if len(title) > 256:
        return jsonify({"error": "Title is too long (max 256 characters)"}), 400
    if description and len(description) > 1024:
        return jsonify({"error": "Description is too long (max 1024 characters)"}), 400

    try:
        repo = g.get_repo(full_name)
        params = {"title": title, "description": description}
        if due_on:
            import datetime
            try:
                params["due_on"] = datetime.datetime.fromisoformat(due_on.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid due_on format. Expected ISO 8601."}), 400

        ms = repo.create_milestone(**params)
        return jsonify({
            "message": "Milestone created successfully",
            "number": ms.number,
            "title": ms.title
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/portfolio/milestones', methods=['GET'])
def workspace_portfolio_milestones():
    token = session.get('github_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    session_id = secure_filename(session.get('session_id', 'default'))
    if not session_id:
        session_id = 'default'
    workspace_root = os.path.join('/tmp/gh-web-workspaces', session_id)

    if not os.path.exists(workspace_root):
        return jsonify([]), 200

    def fetch_repo_milestones(repo_dir):
        repo_path = os.path.join(workspace_root, repo_dir)
        if not os.path.isdir(repo_path):
            return []

        git_path = os.path.join(repo_path, '.git')
        if not os.path.exists(git_path):
            return []

        try:
            repo = git.Repo(repo_path)
            full_name = None
            if 'origin' in repo.remotes:
                full_name = get_repo_full_name_from_url(repo.remotes.origin.url)

            if not full_name:
                return []

            g = Github(auth=github.Auth.Token(token), timeout=30)
            gh_repo = g.get_repo(full_name)
            milestones = gh_repo.get_milestones(state='open')

            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)

            repo_milestones = []
            for ms in milestones:
                total = int(ms.open_issues) + int(ms.closed_issues)
                progress = (int(ms.closed_issues) / total * 100) if total > 0 else 0
                is_overdue = False
                if ms.due_on:
                    # ms.due_on is often naive but usually UTC from PyGithub
                    due = ms.due_on
                    if due.tzinfo is None:
                        due = due.replace(tzinfo=datetime.timezone.utc)
                    is_overdue = due < now

                repo_milestones.append({
                    "repo_name": str(repo_dir),
                    "full_name": str(full_name),
                    "number": int(ms.number),
                    "title": str(ms.title),
                    "description": str(ms.description) if ms.description else "",
                    "open_issues": int(ms.open_issues),
                    "closed_issues": int(ms.closed_issues),
                    "due_on": ms.due_on.isoformat() if ms.due_on else None,
                    "progress": float(progress),
                    "is_overdue": bool(is_overdue),
                    "html_url": str(ms.html_url)
                })
            return repo_milestones
        except Exception:
            return []

    try:
        repo_dirs = sorted(os.listdir(workspace_root))
        # Scalability: Limit the number of repositories to process in a single batch portfolio view
        repo_dirs = repo_dirs[:50]
        aggregated_milestones = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_repo_milestones, rd) for rd in repo_dirs]
            for future in futures:
                res = future.result()
                if res:
                    aggregated_milestones.extend(res)

        # Sort by due_on ascending, nulls last
        def sort_key(ms):
            return (ms['due_on'] is None, ms['due_on'])

        aggregated_milestones.sort(key=sort_key)

        return jsonify(aggregated_milestones), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
