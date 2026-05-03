from flask import Blueprint, request, session, jsonify
import github
from ..workspace.utils import mask_token

bp = Blueprint('deployments', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    auth = github.Auth.Token(token)
    return github.Github(auth=auth)

@bp.route('/api/repos/<path:full_name>/environments', methods=['GET'])
def list_environments(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        environments = repo.get_environments()
        results = []
        for env in environments:
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
        deployments = repo.get_deployments(environment=environment)
        results = []
        for d in deployments:
            # Fetch latest status
            statuses = d.get_statuses()
            latest_status = None
            if statuses.totalCount > 0:
                s = statuses[0]
                latest_status = {
                    "state": s.state,
                    "description": s.description,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "creator": s.creator.login if s.creator else None
                }

            results.append({
                "id": d.id,
                "sha": d.sha,
                "ref": d.ref,
                "task": d.task,
                "environment": d.environment,
                "description": d.description,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                "creator": d.creator.login if d.creator else None,
                "latest_status": latest_status
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

    if not ref or not environment:
        return jsonify({"error": "ref and environment are required"}), 400

    try:
        repo = g.get_repo(full_name)
        deployment = repo.create_deployment(
            ref=ref,
            environment=environment,
            description=description,
            task=task,
            auto_merge=False  # Typically preferred for manual control in GH-Web
        )
        return jsonify({
            "message": "Deployment created successfully",
            "id": deployment.id,
            "environment": deployment.environment
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/deployments/<int:deployment_id>/status', methods=['POST'])
def create_deployment_status(full_name, deployment_id):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    state = data.get('state')  # error, failure, inactive, in_progress, queued, pending, success
    description = data.get('description', '')

    if not state:
        return jsonify({"error": "state is required"}), 400

    try:
        repo = g.get_repo(full_name)
        deployment = repo.get_deployment(deployment_id)
        status = deployment.create_status(state=state, description=description)
        return jsonify({
            "message": f"Deployment status updated to {state}",
            "state": status.state
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
