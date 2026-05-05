from flask import Blueprint, request, session, jsonify
import github
from github import Github
from ..workspace.utils import mask_token

bp = Blueprint('deployments', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(auth=github.Auth.Token(token))

@bp.route('/api/repos/<path:full_name>/environments', methods=['GET'])
def list_environments(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        # Note: PyGithub might have a slightly different method name depending on version
        # repo.get_environments() is standard for v1.55+
        envs = repo.get_environments()
        results = []
        for env in envs:
            results.append({
                "name": env.name,
                "url": env.url,
                "html_url": env.html_url,
                "created_at": env.created_at.isoformat() if env.created_at else None,
                "updated_at": env.updated_at.isoformat() if env.updated_at else None
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/deployments', methods=['GET'])
def list_deployments(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    environment = request.args.get('environment')

    try:
        repo = g.get_repo(full_name)
        params = {}
        if environment:
            params['environment'] = environment

        deployments = repo.get_deployments(**params)
        results = []
        for i, dep in enumerate(deployments):
            if i >= 50: break

            # Fetch latest status
            statuses = dep.get_statuses()
            latest_status = None
            for status in statuses:
                latest_status = {
                    "state": status.state,
                    "description": status.description,
                    "updated_at": status.updated_at.isoformat() if status.updated_at else None
                }
                break # get_statuses returns them in reverse chronological order

            results.append({
                "id": dep.id,
                "sha": dep.sha,
                "ref": dep.ref,
                "task": dep.task,
                "environment": dep.environment,
                "description": dep.description,
                "created_at": dep.created_at.isoformat() if dep.created_at else None,
                "updated_at": dep.updated_at.isoformat() if dep.updated_at else None,
                "latest_status": latest_status,
                "creator": dep.creator.login if dep.creator else None
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/deployments', methods=['POST'])
def create_deployment(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    ref = data.get('ref')
    environment = data.get('environment')
    description = data.get('description', 'Deployed via GH-Web')
    task = data.get('task', 'deploy')
    payload = data.get('payload', {})

    if not ref or not environment:
        return jsonify({"error": "ref and environment are required"}), 400

    try:
        repo = g.get_repo(full_name)
        deployment = repo.create_deployment(
            ref=ref,
            environment=environment,
            description=description,
            task=task,
            payload=payload,
            auto_merge=False # Often preferred for manual triggers
        )
        return jsonify({
            "message": f"Deployment to {environment} triggered successfully",
            "id": deployment.id,
            "sha": deployment.sha
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
