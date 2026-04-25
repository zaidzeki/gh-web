import os
import shutil
import git
import tempfile
from flask import Blueprint, request, session, jsonify
from github import Github
from werkzeug.utils import secure_filename
from ..workspace.utils import render_template_dir

bp = Blueprint('repos', __name__)

def mask_token(s):
    token = session.get('github_token')
    if token and isinstance(s, str):
        return s.replace(token, '********')
    return s

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(token)

@bp.route('/api/repos', methods=['GET'])
def list_repos():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    search_query = request.args.get('search')

    try:
        user = g.get_user()
        if search_query:
            # Filtered search within user's context
            repos = g.search_repositories(f"user:{user.login} {search_query}")
        else:
            # Default to recently pushed
            repos = user.get_repos(sort='pushed', direction='desc')

        results = []
        # Pre-fetch PR counts using Search API to avoid N+1 problem
        # Search query: "is:pr is:open user:LOGIN" returns all open PRs in user's repos
        pr_counts = {}
        try:
            open_prs = g.search_issues(f"is:pr is:open user:{user.login}")
            for pr in open_prs:
                # Extract repo full name from pull_request.html_url or repository.full_name
                # search_issues returns Issue objects (which PRs are a subset of)
                repo_name = pr.repository.full_name
                pr_counts[repo_name] = pr_counts.get(repo_name, 0) + 1
        except Exception:
            # Fallback to 0 if search fails
            pass

        for i, repo in enumerate(repos):
            if i >= 30: break
            results.append({
                "full_name": repo.full_name,
                "name": repo.name,
                "description": repo.description,
                "html_url": repo.html_url,
                "stargazers_count": repo.stargazers_count,
                "open_issues_count": repo.open_issues_count,
                "open_prs_count": pr_counts.get(repo.full_name, 0),
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "private": repo.private
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

    data = request.get_json() or request.form
    name = data.get('name')
    description = data.get('description', '')
    visibility = data.get('visibility', 'public')
    private = visibility == 'private'

    if not name:
        return jsonify({"error": "Repository name is required"}), 400

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

    try:
        user = g.get_user()
        repo = user.create_repo(
            name,
            description=description,
            private=private
        )

        if template_name:
            templates_root = os.path.expanduser('~/.zekiprod/templates')
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
