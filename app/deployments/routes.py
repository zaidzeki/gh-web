from flask import Blueprint, request, session, jsonify
from github import Github, Auth
from ..workspace.utils import mask_token

bp = Blueprint('deployments', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    # Use Auth.Token as per 2025-05-23 journal entry
    auth = Auth.Token(token)
    return Github(auth=auth)

@bp.route('/api/repos/<path:full_name>/environments', methods=['GET'])
def list_environments(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        envs = repo.get_environments()
        results = []
        for env in envs:
            results.append({
                "id": env.id,
                "name": env.name,
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
        deployments = repo.get_deployments(environment=environment)
        results = []
        for dep in deployments:
            # Get latest status
            statuses = dep.get_statuses()
            latest_status = None
            if statuses.totalCount > 0:
                s = statuses[0]
                latest_status = {
                    "state": s.state,
                    "description": s.description,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }

            results.append({
                "id": dep.id,
                "environment": dep.environment,
                "ref": dep.ref,
                "sha": dep.sha,
                "task": dep.task,
                "description": dep.description,
                "created_at": dep.created_at.isoformat() if dep.created_at else None,
                "updated_at": dep.updated_at.isoformat() if dep.updated_at else None,
                "latest_status": latest_status,
                "creator": {
                    "login": dep.creator.login,
                    "avatar_url": dep.creator.avatar_url
                } if dep.creator else None
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

    if not ref or not environment:
        return jsonify({"error": "ref and environment are required"}), 400

    try:
        repo = g.get_repo(full_name)
        deployment = repo.create_deployment(
            ref=ref,
            environment=environment,
            description=description,
            auto_merge=False # Common for manual triggers
        )
        return jsonify({
            "message": f"Deployment to {environment} created successfully",
            "id": deployment.id
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
