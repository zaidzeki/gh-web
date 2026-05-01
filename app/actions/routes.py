from flask import Blueprint, request, session, jsonify
import github
from github import Github
from ..workspace.utils import mask_token

bp = Blueprint('actions', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(auth=github.Auth.Token(token))

@bp.route('/api/repos/<path:full_name>/actions/workflows', methods=['GET'])
def list_workflows(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        workflows = repo.get_workflows()
        results = []
        for wf in workflows:
            results.append({
                "id": wf.id,
                "name": wf.name,
                "state": wf.state,
                "path": wf.path,
                "html_url": wf.html_url
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/actions/runs', methods=['GET'])
def list_runs(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    status = request.args.get('status')
    branch = request.args.get('branch')
    workflow_id = request.args.get('workflow_id')

    try:
        repo = g.get_repo(full_name)
        params = {}
        if status: params['status'] = status
        if branch: params['branch'] = branch

        if workflow_id:
            workflow = repo.get_workflow(workflow_id)
            runs = workflow.get_runs(**params)
        else:
            runs = repo.get_workflow_runs(**params)

        results = []
        for i, run in enumerate(runs):
            if i >= 50: break  # Limit to last 50 runs
            results.append({
                "id": run.id,
                "name": run.name,
                "status": run.status,
                "conclusion": run.conclusion,
                "branch": run.head_branch,
                "sha": run.head_sha,
                "html_url": run.html_url,
                "updated_at": run.updated_at.isoformat() if run.updated_at else None,
                "run_number": run.run_number
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/actions/workflows/<int:workflow_id>/dispatch', methods=['POST'])
def dispatch_workflow(full_name, workflow_id):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    ref = data.get('ref', 'main')
    inputs = data.get('inputs', {})

    try:
        repo = g.get_repo(full_name)
        workflow = repo.get_workflow(str(workflow_id))
        success = workflow.create_dispatch(ref, inputs)
        if success:
            return jsonify({"message": f"Workflow {workflow_id} dispatched successfully on {ref}"}), 200
        else:
            return jsonify({"error": "Failed to dispatch workflow"}), 400
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
