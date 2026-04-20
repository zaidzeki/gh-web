from flask import Blueprint, request, session, jsonify
from github import Github

bp = Blueprint('prs', __name__)

def mask_token(s):
    token = session.get('github_token')
    if token and isinstance(s, str):
        return s.replace(token, '********')
    return s

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(token)

@bp.route('/api/repos/<path:full_name>/prs', methods=['GET'])
def list_prs(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        prs = repo.get_pulls(state='all')
        return jsonify([{
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "html_url": pr.html_url,
            "user": pr.user.login
        } for pr in prs]), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/prs', methods=['POST'])
def create_pr(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    title = data.get('title')
    body = data.get('body', '')
    head = data.get('head')
    base = data.get('base')

    if not title or not head or not base:
        return jsonify({"error": "title, head, and base are required"}), 400

    try:
        repo = g.get_repo(full_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        return jsonify({
            "message": "Pull Request created successfully",
            "number": pr.number,
            "html_url": pr.html_url
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/prs/<int:pr_number>/merge', methods=['POST'])
def merge_pr(full_name, pr_number):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    commit_message = data.get('commit_message', '')
    merge_method = data.get('merge_method', 'merge')

    try:
        repo = g.get_repo(full_name)
        pr = repo.get_pull(pr_number)
        status = pr.merge(commit_message=commit_message, merge_method=merge_method)
        if status.merged:
            return jsonify({"message": "Pull Request merged successfully"}), 200
        else:
            return jsonify({"error": "Failed to merge Pull Request"}), 400
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
