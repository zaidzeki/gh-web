import requests
from flask import Blueprint, request, session, jsonify
from github import Github, Auth
from ..workspace.utils import mask_token

bp = Blueprint('deployments', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    auth = Auth.Token(token)
    # Security Enhancement: Add timeout to prevent resource exhaustion from hanging API calls
    return Github(auth=auth, timeout=30)

@bp.route('/api/repos/<path:full_name>/environments', methods=['GET'])
def list_environments(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        # PyGithub get_environments() returns a PaginatedList of Environment objects
        envs = repo.get_environments()

        # Pre-fetch recent deployments to enrich environment data without N+1 per-env calls
        # Scalability: Scan only the most recent 100 deployments to avoid performance issues
        deployments = repo.get_deployments()
        latest_deps = {}
        for i, d in enumerate(deployments):
            if i >= 100: break # Safety limit on scan depth
            if d.environment not in latest_deps:
                # Fetch latest status for this deployment
                statuses = d.get_statuses()
                latest_status = None
                for s in statuses:
                    latest_status = {
                        "state": str(s.state),
                        "description": str(s.description) if s.description else "",
                        "updated_at": s.updated_at.isoformat() if s.updated_at else None
                    }
                    break

                latest_deps[d.environment] = {
                    "id": d.id,
                    "sha": str(d.sha),
                    "ref": str(d.ref),
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "creator": str(d.creator.login) if d.creator else None,
                    "latest_status": latest_status
                }
            if len(latest_deps) > 20: break # Cap enrichment for performance

        results = []
        for env in envs:
            results.append({
                "name": str(env.name),
                "html_url": str(env.html_url),
                "created_at": env.created_at.isoformat() if env.created_at else None,
                "updated_at": env.updated_at.isoformat() if env.updated_at else None,
                "latest_deployment": latest_deps.get(env.name)
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

@bp.route('/api/repos/<path:full_name>/actions/runs/<int:run_id>/review', methods=['POST'])
def review_deployment(full_name, run_id):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    event = data.get('event') # 'approve' or 'reject'
    comment = data.get('comment', '')

    if event not in ['approve', 'reject']:
        return jsonify({"error": "event must be 'approve' or 'reject'"}), 400

    try:
        # We need to find the pending deployment environment names for this run
        # Using raw request because PyGithub might not support this yet in the version we have
        # GET /repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments

        token = session.get('github_token')
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        pending_url = f"https://api.github.com/repos/{full_name}/actions/runs/{run_id}/pending_deployments"
        # Security Enhancement: Add timeout to prevent resource exhaustion
        resp = requests.get(pending_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            return jsonify({"error": mask_token(f"Failed to fetch pending deployments: {resp.text}")}), resp.status_code

        pending_data = resp.json()
        # pending_data is expected to be a list according to documentation or an object with 'pending_deployments' key
        # Based on Orchestra guide: {"total_count": 1, "pending_deployments": [...]}
        pending_list = pending_data if isinstance(pending_data, list) else pending_data.get('pending_deployments', [])

        env_ids = [d['environment']['id'] for d in pending_list if 'environment' in d and 'id' in d['environment']]

        if not env_ids:
            return jsonify({"error": "No pending deployments found for this run"}), 404

        # POST /repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments
        review_url = f"https://api.github.com/repos/{full_name}/actions/runs/{run_id}/pending_deployments"
        review_payload = {
            "environment_ids": env_ids,
            "state": event,
            "comment": comment
        }

        # Security Enhancement: Add timeout to prevent resource exhaustion
        resp = requests.post(review_url, headers=headers, json=review_payload, timeout=30)
        if resp.status_code in [200, 201, 204]:
            return jsonify({"message": f"Deployment {event}d successfully"}), 200
        else:
            return jsonify({"error": mask_token(f"Failed to review deployment: {resp.text}")}), resp.status_code

    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
