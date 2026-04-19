import os
import shutil
import zipfile
import tarfile
import subprocess
from flask import Blueprint, request, session, jsonify, current_app
from github import Github
import git
from werkzeug.utils import secure_filename

bp = Blueprint('workspace', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(token)

def get_workspace_dir(repo_name):
    session_id = session.get('session_id', 'default')
    workspace_root = os.path.join('/tmp/gh-web-workspaces', session_id)
    repo_workspace = os.path.join(workspace_root, repo_name)
    os.makedirs(repo_workspace, exist_ok=True)
    return repo_workspace

def is_safe_path(basedir, path, follow_symlinks=True):
    if follow_symlinks:
        matchpath = os.path.realpath(path)
    else:
        matchpath = os.path.abspath(path)
    return matchpath.startswith(os.path.realpath(basedir))

@bp.before_app_request
def ensure_session_id():
    if 'session_id' not in session:
        import uuid
        session['session_id'] = str(uuid.uuid4())

@bp.route('/api/workspace/clone', methods=['POST'])
def clone_repo():
    token = session.get('github_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    repo_url = data.get('repo_url')
    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    repo_name = repo_url.split('/')[-1].replace('.git', '')
    workspace_dir = get_workspace_dir(repo_name)

    if os.path.exists(os.path.join(workspace_dir, '.git')):
        session['active_repo'] = repo_name
        return jsonify({"message": "Repository already cloned", "path": workspace_dir}), 200

    try:
        if repo_url.startswith('https://github.com/'):
            auth_url = repo_url.replace('https://github.com/', f'https://{token}@github.com/')
        else:
            auth_url = repo_url

        git.Repo.clone_from(auth_url, workspace_dir)
        session['active_repo'] = repo_name
        return jsonify({"message": "Repository cloned successfully", "path": workspace_dir}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/workspace/download', methods=['POST'])
def download_repo():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    repo_name_full = data.get('repo_name')
    ref = data.get('ref', 'main')

    if not repo_name_full:
        return jsonify({"error": "repo_name is required"}), 400

    repo_name = repo_name_full.split('/')[-1]
    workspace_dir = get_workspace_dir(repo_name)

    try:
        repo = g.get_repo(repo_name_full)
        archive_link = repo.get_archive_link('zipball', ref)
        import httpx
        with httpx.stream("GET", archive_link, follow_redirects=True) as r:
            archive_path = os.path.join(workspace_dir, 'repo.zip')
            with open(archive_path, 'wb') as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)

        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(workspace_dir)

        os.remove(archive_path)
        session['active_repo'] = repo_name
        return jsonify({"message": "Repository downloaded and extracted successfully", "path": workspace_dir}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/workspace/modify/patch', methods=['POST'])
def apply_patch():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)

    if 'file' not in request.files:
        return jsonify({"error": "No patch file provided"}), 400

    patch_file = request.files['file']
    if patch_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(patch_file.filename)
    patch_path = os.path.join(workspace_dir, filename)
    patch_file.save(patch_path)

    try:
        if os.path.exists(os.path.join(workspace_dir, '.git')):
            repo = git.Repo(workspace_dir)
            repo.git.apply(filename)
        else:
            subprocess.run(['patch', '-p1', '-i', filename], cwd=workspace_dir, check=True)

        os.remove(patch_path)
        return jsonify({"message": "Patch applied successfully"}), 200
    except Exception as e:
        if os.path.exists(patch_path):
            os.remove(patch_path)
        return jsonify({"error": str(e)}), 500

@bp.route('/api/workspace/modify/upload', methods=['POST'])
def upload_file():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    target_path = request.form.get('target_path', '')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    full_target_dir = os.path.join(workspace_dir, target_path)
    if not is_safe_path(workspace_dir, full_target_dir):
        return jsonify({"error": "Invalid target path"}), 400

    os.makedirs(full_target_dir, exist_ok=True)
    file_path = os.path.join(full_target_dir, filename)
    file.save(file_path)

    return jsonify({"message": f"File {filename} uploaded successfully to {target_path}"}), 200

@bp.route('/api/workspace/modify/archive', methods=['POST'])
def upload_archive():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)

    if 'archive' not in request.files:
        return jsonify({"error": "No archive provided"}), 400

    archive = request.files['archive']
    target_cwd = request.form.get('target_cwd', '.')

    if archive.filename == '':
        return jsonify({"error": "No selected archive"}), 400

    filename = secure_filename(archive.filename)
    full_target_dir = os.path.join(workspace_dir, target_cwd)
    if not is_safe_path(workspace_dir, full_target_dir):
        return jsonify({"error": "Invalid target CWD"}), 400

    os.makedirs(full_target_dir, exist_ok=True)
    archive_path = os.path.join(workspace_dir, filename)
    archive.save(archive_path)

    try:
        if filename.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    member_path = os.path.join(full_target_dir, member)
                    if not is_safe_path(full_target_dir, member_path):
                        raise Exception(f"Potential Zip Slip detected: {member}")
                zip_ref.extractall(full_target_dir)
        elif filename.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                for member in tar_ref.getmembers():
                    member_path = os.path.join(full_target_dir, member.name)
                    if not is_safe_path(full_target_dir, member_path):
                        raise Exception(f"Potential Tar Slip detected: {member.name}")
                tar_ref.extractall(full_target_dir)
        else:
            return jsonify({"error": "Unsupported archive format"}), 400

        os.remove(archive_path)
        return jsonify({"message": "Archive extracted successfully"}), 200
    except Exception as e:
        if os.path.exists(archive_path):
            os.remove(archive_path)
        return jsonify({"error": str(e)}), 500

@bp.route('/api/workspace/commit', methods=['POST'])
def commit_changes():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    if not os.path.exists(os.path.join(workspace_dir, '.git')):
        return jsonify({"error": "Active workspace is not a git repository"}), 400

    data = request.get_json() or request.form
    commit_message = data.get('commit_message')
    if not commit_message:
        return jsonify({"error": "commit_message is required"}), 400

    try:
        repo = git.Repo(workspace_dir)

        # Configure Git identity if not set
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "GH-Web User")
            cw.set_value("user", "email", "gh-web@example.com")

        repo.git.add(all=True)
        repo.index.commit(commit_message)
        return jsonify({"message": "Changes committed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
