from flask import Blueprint, request, session, jsonify
from github import Github, Auth
from ..workspace.utils import mask_token

bp = Blueprint('deployments', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
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
        params = {}
        if environment:
            params['environment'] = environment

        deployments = repo.get_deployments(**params)
        results = []
        for d in deployments:
            # Fetch latest status
            statuses = d.get_statuses()
            latest_status = statuses[0] if statuses.totalCount > 0 else None

            results.append({
                "id": d.id,
                "environment": d.environment,
                "ref": d.ref,
                "sha": d.sha,
                "task": d.task,
                "description": d.description,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                "creator": d.creator.login if d.creator else None,
                "state": latest_status.state if latest_status else "pending",
                "status_description": latest_status.description if latest_status else None
            })
            if len(results) >= 50: break # Limit to 50
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
            auto_merge=False,
            required_contexts=[] # Allow deployment regardless of CI status for now, or we can make this configurable
        )
        return jsonify({
            "message": "Deployment created successfully",
            "id": deployment.id
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
