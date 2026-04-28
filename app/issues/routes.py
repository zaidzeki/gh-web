from flask import Blueprint, request, session, jsonify
from github import Github
from ..workspace.utils import mask_token

bp = Blueprint('issues', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(token)

@bp.route('/api/repos/<path:full_name>/issues/<int:issue_number>/comments', methods=['GET'])
def get_comments(full_name, issue_number):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        issue = repo.get_issue(issue_number)
        comments = issue.get_comments()
        results = []
        for comment in comments:
            results.append({
                "user": comment.user.login,
                "avatar_url": comment.user.avatar_url,
                "body": comment.body,
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/issues', methods=['GET'])
def list_issues(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        # get_issues returns both issues and PRs by default
        issues = repo.get_issues(state='open')
        results = []
        for issue in issues:
            # GitHub API returns PRs as issues, but they have a 'pull_request' attribute
            if issue.pull_request is None:
                results.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "html_url": issue.html_url,
                    "user": issue.user.login,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None
                })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/issues/<int:issue_number>/comments', methods=['POST'])
def post_comment(full_name, issue_number):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    body = data.get('body')

    if not body:
        return jsonify({"error": "Comment body is required"}), 400

    try:
        repo = g.get_repo(full_name)
        issue = repo.get_issue(issue_number)
        comment = issue.create_comment(body)
        return jsonify({
            "message": "Comment posted successfully",
            "user": comment.user.login,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/issues', methods=['POST'])
def create_issue(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    title = data.get('title')
    body = data.get('body', '')

    if not title:
        return jsonify({"error": "title is required"}), 400

    try:
        repo = g.get_repo(full_name)
        issue = repo.create_issue(title=title, body=body)
        return jsonify({
            "message": "Issue created successfully",
            "number": issue.number,
            "html_url": issue.html_url
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/issues/<int:issue_number>/close', methods=['POST'])
def close_issue(full_name, issue_number):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        issue = repo.get_issue(issue_number)
        issue.edit(state='closed')
        return jsonify({"message": f"Issue #{issue_number} closed successfully"}), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
