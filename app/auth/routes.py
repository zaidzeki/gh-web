from flask import Blueprint, request, session, jsonify

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    token = request.form.get('token')
    if not token:
        return jsonify({"error": "Token is required"}), 400

    session['github_token'] = token
    return jsonify({"message": "Logged in successfully"}), 200
