from flask import Blueprint, request, session, jsonify
from github import Github

bp = Blueprint('repos', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(token)

@bp.route('/api/repos', methods=['POST'])
@bp.route('/api/repos/create', methods=['POST'])
def create_repo():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    name = data.get('name')
    description = data.get('description', '')
    visibility = data.get('visibility', 'public')
    private = visibility == 'private'

    if not name:
        return jsonify({"error": "Repository name is required"}), 400

    try:
        user = g.get_user()
        repo = user.create_repo(
            name,
            description=description,
            private=private
        )
        return jsonify({
            "message": f"Repository {name} created successfully",
            "full_name": repo.full_name,
            "clone_url": repo.clone_url
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
