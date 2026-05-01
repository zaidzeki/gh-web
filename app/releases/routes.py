from flask import Blueprint, request, session, jsonify
from github import Github, Auth
from ..workspace.utils import mask_token

bp = Blueprint('releases', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    auth = Auth.Token(token)
    return Github(auth=auth)

@bp.route('/api/repos/<path:full_name>/releases', methods=['GET'])
def list_releases(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        releases = repo.get_releases()
        return jsonify([{
            "id": r.id,
            "tag_name": r.tag_name,
            "name": r.title,
            "body": r.body,
            "draft": r.draft,
            "prerelease": r.prerelease,
            "html_url": r.html_url,
            "published_at": r.published_at.isoformat() if r.published_at else None
        } for r in releases]), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/releases/generate-notes', methods=['POST'])
def generate_release_notes(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    tag_name = data.get('tag_name')
    target_commitish = data.get('target_commitish') or None
    previous_tag_name = data.get('previous_tag_name') or None

    if not tag_name:
        return jsonify({"error": "tag_name is required"}), 400

    try:
        repo = g.get_repo(full_name)
        notes = repo.generate_release_notes(
            tag_name=tag_name,
            target_commitish=target_commitish,
            previous_tag_name=previous_tag_name
        )
        return jsonify({
            "name": notes.name,
            "body": notes.body
        }), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/releases', methods=['POST'])
def create_release(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    tag_name = data.get('tag_name')
    name = data.get('name')
    body = data.get('body', '')
    draft = data.get('draft') in [True, 'true', 'on', '1']
    prerelease = data.get('prerelease') in [True, 'true', 'on', '1']
    target_commitish = data.get('target_commitish') or None

    if not tag_name or not name:
        return jsonify({"error": "tag_name and name are required"}), 400

    try:
        repo = g.get_repo(full_name)
        release = repo.create_git_release(
            tag=tag_name,
            name=name,
            message=body,
            draft=draft,
            prerelease=prerelease,
            target_commitish=target_commitish
        )
        return jsonify({
            "message": "Release created successfully",
            "id": release.id,
            "html_url": release.html_url
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
