from flask import Blueprint, request, session, jsonify
import github
from github import Github
from ..workspace.utils import mask_token

bp = Blueprint('milestones', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    # Security Enhancement: Add timeout to prevent resource exhaustion from hanging API calls
    return Github(auth=github.Auth.Token(token), timeout=30)

@bp.route('/api/repos/<path:full_name>/milestones', methods=['GET'])
def list_milestones(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    state = request.args.get('state', 'open')

    try:
        repo = g.get_repo(full_name)
        milestones = repo.get_milestones(state=state)
        results = []
        for ms in milestones:
            results.append({
                "number": int(ms.number),
                "title": str(ms.title),
                "description": str(ms.description) if ms.description else "",
                "state": str(ms.state),
                "open_issues": int(ms.open_issues),
                "closed_issues": int(ms.closed_issues),
                "due_on": ms.due_on.isoformat() if ms.due_on else None,
                "html_url": str(ms.html_url)
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/milestones', methods=['POST'])
def create_milestone(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    title = data.get('title')
    description = data.get('description', '')
    due_on = data.get('due_on') # Expected in ISO format if provided

    if not title:
        return jsonify({"error": "Milestone title is required"}), 400

    try:
        repo = g.get_repo(full_name)
        params = {"title": title, "description": description}
        if due_on:
            import datetime
            try:
                params["due_on"] = datetime.datetime.fromisoformat(due_on.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid due_on format. Expected ISO 8601."}), 400

        ms = repo.create_milestone(**params)
        return jsonify({
            "message": "Milestone created successfully",
            "number": ms.number,
            "title": ms.title
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
