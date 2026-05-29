import os
import mimetypes
from flask import Blueprint, request, session, jsonify
from github import Github, Auth
from ..workspace.utils import mask_token, get_workspace_dir, is_safe_path

bp = Blueprint('releases', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    auth = Auth.Token(token)
    # Security Enhancement: Add timeout to prevent resource exhaustion from hanging API calls
    return Github(auth=auth, timeout=30)

@bp.route('/api/repos/<path:full_name>/releases', methods=['GET'])
def list_releases(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        releases = repo.get_releases()
        # Security Enhancement: Limit to first 100 items to prevent DoS/resource exhaustion
        results = []
        for i, r in enumerate(releases):
            if i >= 100: break

            # Use pre-fetched assets attribute to avoid N+1 API calls
            try:
                assets_count = len(r.assets)
            except Exception:
                assets_count = 0

            results.append({
                "id": r.id,
                "tag_name": r.tag_name,
                "name": r.title,
                "body": r.body,
                "draft": r.draft,
                "prerelease": r.prerelease,
                "html_url": r.html_url,
                "published_at": r.published_at.isoformat() if r.published_at else None,
                "assets_count": assets_count
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/releases/<int:release_id>/assets', methods=['GET'])
def list_release_assets(full_name, release_id):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        release = repo.get_release(release_id)
        assets = release.get_assets()

        results = []
        for i, a in enumerate(assets):
            if i >= 100: break
            results.append({
                "id": a.id,
                "name": a.name,
                "label": a.label,
                "size": a.size,
                "download_count": a.download_count,
                "created_at": a.created_at.isoformat(),
                "browser_download_url": a.browser_download_url
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/releases/<int:release_id>/assets', methods=['POST'])
def upload_release_asset(full_name, release_id):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or request.form
    workspace_path = data.get('workspace_path')
    name = data.get('name')
    label = data.get('label', '')

    if not workspace_path:
        return jsonify({"error": "workspace_path is required"}), 400

    repo_name = full_name.split('/')[-1]
    try:
        workspace_dir = get_workspace_dir(repo_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    full_path = os.path.join(workspace_dir, workspace_path)
    if not is_safe_path(workspace_dir, full_path) or not os.path.isfile(full_path):
        return jsonify({"error": "Invalid workspace file path"}), 400

    if not name:
        name = os.path.basename(full_path)

    try:
        repo = g.get_repo(full_name)
        release = repo.get_release(release_id)

        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = 'application/octet-stream'

        # PyGithub's upload_asset takes the path and handles streaming
        asset = release.upload_asset(
            path=full_path,
            label=label,
            name=name,
            content_type=content_type
        )

        return jsonify({
            "message": "Asset uploaded successfully",
            "id": asset.id,
            "name": asset.name,
            "browser_download_url": asset.browser_download_url
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/releases/assets/<int:asset_id>', methods=['DELETE'])
def delete_release_asset(full_name, asset_id):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = g.get_repo(full_name)
        # GitReleaseAsset doesn't have a direct way to be deleted from repo object easily in PyGithub
        # without first getting the release, but we can try to use raw API or just get the asset
        # Actually PyGithub has repo.get_release_asset(id)
        asset = repo.get_release_asset(asset_id)
        asset.delete_asset()
        return jsonify({"message": "Asset deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/releases/generate-notes', methods=['POST'])
def generate_release_notes(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or request.form
    tag_name = data.get('tag_name')
    target_commitish = data.get('target_commitish') or None
    previous_tag_name = data.get('previous_tag_name') or None

    if not tag_name:
        return jsonify({"error": "tag_name is required"}), 400

    # Security Enhancement: Input length validation
    if len(tag_name) > 255:
        return jsonify({"error": "Tag name is too long (max 255 characters)"}), 400
    if target_commitish and len(target_commitish) > 255:
        return jsonify({"error": "Target commitish is too long (max 255 characters)"}), 400
    if previous_tag_name and len(previous_tag_name) > 255:
        return jsonify({"error": "Previous tag name is too long (max 255 characters)"}), 400

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

    data = request.get_json(silent=True) or request.form
    tag_name = data.get('tag_name')
    name = data.get('name')
    body = data.get('body', '')
    draft = data.get('draft') in [True, 'true', 'on', '1']
    prerelease = data.get('prerelease') in [True, 'true', 'on', '1']
    target_commitish = data.get('target_commitish') or None

    if not tag_name or not name:
        return jsonify({"error": "tag_name and name are required"}), 400

    # Security Enhancement: Input length validation
    if len(tag_name) > 255:
        return jsonify({"error": "Tag name is too long (max 255 characters)"}), 400
    if len(name) > 255:
        return jsonify({"error": "Release name is too long (max 255 characters)"}), 400
    if body and len(body) > 65536:
        return jsonify({"error": "Release body is too long (max 65536 characters)"}), 400

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
