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
                "html_url": f"https://github.com/{full_name}/settings/environments" # PyGithub doesn't easily expose the env settings URL
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
            if len(results) >= 50: break # Limit

            # Fetch latest status
            statuses = d.get_statuses()
            latest_status = None
            if statuses.totalCount > 0:
                s = statuses[0]
                latest_status = {
                    "state": s.state,
                    "description": s.description,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }

            results.append({
                "id": d.id,
                "environment": d.environment,
                "ref": d.ref,
                "sha": d.sha,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                "creator": d.creator.login if d.creator else None,
                "latest_status": latest_status,
                "description": d.description
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
            auto_merge=False, # Standard for these types of tools
            required_contexts=[] # Allow deployment even if checks haven't finished (can be tuned)
        )
        return jsonify({
            "message": f"Deployment to {environment} triggered successfully",
            "id": deployment.id
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/deployments/<int:deployment_id>/status', methods=['POST'])
def update_deployment_status(full_name, deployment_id):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    state = data.get('state')
    description = data.get('description', '')

    if not state:
        return jsonify({"error": "state is required"}), 400

    try:
        repo = g.get_repo(full_name)
        deployment = repo.get_deployment(deployment_id)
        status = deployment.create_status(state=state, description=description)
        return jsonify({
            "message": f"Deployment status updated to {state}",
            "id": status.id
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
