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
            latest_deployment = None
            deployments = repo.get_deployments(environment=env.name)
            # get_deployments returns a PaginatedList, sorted by created_at desc by default usually
            for d in deployments:
                latest_deployment = d
                break

            status = None
            if latest_deployment:
                statuses = latest_deployment.get_statuses()
                for s in statuses:
                    status = {
                        "state": s.state,
                        "description": s.description,
                        "updated_at": s.updated_at.isoformat() if s.updated_at else None
                    }
                    break

            results.append({
                "name": env.name,
                "html_url": env.html_url,
                "latest_deployment": {
                    "id": latest_deployment.id,
                    "ref": latest_deployment.ref,
                    "sha": latest_deployment.sha,
                    "task": latest_deployment.task,
                    "environment": latest_deployment.environment,
                    "created_at": latest_deployment.created_at.isoformat() if latest_deployment.created_at else None,
                    "status": status
                } if latest_deployment else None
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
            if len(results) >= 30: break

            status = None
            statuses = d.get_statuses()
            for s in statuses:
                status = {
                    "state": s.state,
                    "description": s.description,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None
                }
                break

            results.append({
                "id": d.id,
                "ref": d.ref,
                "sha": d.sha,
                "task": d.task,
                "environment": d.environment,
                "description": d.description,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "creator": d.creator.login if d.creator else None,
                "status": status
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/deployments', methods=['POST'])
def create_deployment(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or request.form
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
            auto_merge=False # Typically safer for GH-Web
        )
        return jsonify({
            "message": f"Deployment to {environment} created successfully",
            "id": deployment.id
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
