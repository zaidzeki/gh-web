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
        # PyGithub get_environments() returns a PaginatedList of Environment objects
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
        for i, d in enumerate(deployments):
            if i >= 50: break

            # Fetch latest status for each deployment
            statuses = d.get_statuses()
            latest_status = None
            for s in statuses:
                latest_status = {
                    "state": s.state,
                    "description": s.description,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None
                }
                break # get_statuses is usually sorted by newest first?

            results.append({
                "id": d.id,
                "sha": d.sha,
                "ref": d.ref,
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
    description = data.get('description', '')
    task = data.get('task', 'deploy')
    auto_merge = data.get('auto_merge') in [True, 'true', 'on', '1']
    required_contexts = data.get('required_contexts') # Expecting a list if provided

    if not ref or not environment:
        return jsonify({"error": "ref and environment are required"}), 400

    try:
        repo = g.get_repo(full_name)
        deployment = repo.create_deployment(
            ref=ref,
            environment=environment,
            description=description,
            task=task,
            auto_merge=auto_merge,
            required_contexts=required_contexts if isinstance(required_contexts, list) else None
        )
        return jsonify({
            "message": f"Deployment created successfully in {environment}",
            "id": deployment.id,
            "sha": deployment.sha
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
