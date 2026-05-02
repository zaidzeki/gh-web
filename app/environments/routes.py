from flask import Blueprint, request, session, jsonify
import github
from github import Github
from ..workspace.utils import mask_token

bp = Blueprint('environments', __name__)

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
        environments = repo.get_environments()
        results = []
        for env in environments:
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
        params = {}
        if environment:
            params['environment'] = environment

        deployments = repo.get_deployments(**params)
        results = []
        for i, dep in enumerate(deployments):
            if i >= 50: break  # Limit to last 50 deployments

            # Fetch latest status
            status = "unknown"
            try:
                statuses = dep.get_statuses()
                if statuses.totalCount > 0:
                    status = statuses[0].state
            except Exception as status_err:
                # Log or handle status fetch error
                pass

            results.append({
                "id": dep.id,
                "sha": dep.sha,
                "ref": dep.ref,
                "task": dep.task,
                "environment": dep.environment,
                "description": dep.description,
                "creator": dep.creator.login if dep.creator else None,
                "created_at": dep.created_at.isoformat() if dep.created_at else None,
                "updated_at": dep.updated_at.isoformat() if dep.updated_at else None,
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
            required_contexts=required_contexts
        )
        return jsonify({
            "message": f"Deployment to {environment} created successfully",
            "id": deployment.id
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
