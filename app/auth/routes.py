from flask import Blueprint, request, session, jsonify
import github
from github import Github
from ..workspace.utils import mask_token

bp = Blueprint('auth', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    # Security Enhancement: Add timeout to prevent resource exhaustion from hanging API calls
    return Github(auth=github.Auth.Token(token), timeout=30)

@bp.route('/login', methods=['POST'])
def login():
    token = request.form.get('token')
    if not token:
        return jsonify({"error": "Token is required"}), 400

    # Security Enhancement: Clear session before login to prevent session leakage from previous users
    session.clear()
    session['github_token'] = token
    return jsonify({"message": "Logged in successfully"}), 200

@bp.route('/api/user', methods=['GET'])
def get_user_profile():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user = g.get_user()
        return jsonify({
            "login": user.login,
            "avatar_url": user.avatar_url,
            "name": user.name,
            "html_url": user.html_url
        }), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
