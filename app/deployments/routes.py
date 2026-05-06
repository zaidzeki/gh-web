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
        # get_environments() returns a PaginatedList of Environment objects
        envs = repo.get_environments()
        return jsonify([{"name": e.name} for e in envs]), 200
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
        # get_deployments() returns a PaginatedList of Deployment objects
        kwargs = {}
        if environment:
            kwargs['environment'] = environment

        deployments = repo.get_deployments(**kwargs)
        results = []
        for i, d in enumerate(deployments):
            if i >= 50: break
            # Fetch latest status
            statuses = d.get_statuses()
            latest_status = "unknown"
            if statuses.totalCount > 0:
                latest_status = statuses[0].state

            results.append({
                "id": d.id,
                "environment": d.environment,
                "state": latest_status,
                "ref": d.ref,
                "sha": d.sha,
                "description": d.description,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                "creator": d.creator.login if d.creator else None
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
            auto_merge=False
        )
        return jsonify({
            "message": "Deployment created successfully",
            "id": deployment.id
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
