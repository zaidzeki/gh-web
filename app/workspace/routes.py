import os
import shutil
import zipfile
import tarfile
import subprocess
import re
from flask import Blueprint, request, session, jsonify, current_app
from github import Github
import git
from werkzeug.utils import secure_filename
from .utils import get_template_manifest, render_template_dir, is_safe_path

bp = Blueprint('workspace', __name__)

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

def get_workspace_dir(repo_name):
    session_id = secure_filename(session.get('session_id', 'default'))
    workspace_root = os.path.join('/tmp/gh-web-workspaces', session_id)
    # Sanitize repo_name to prevent path traversal via malicious repository names
    safe_repo_name = secure_filename(repo_name)
    repo_workspace = os.path.join(workspace_root, safe_repo_name)
    os.makedirs(repo_workspace, exist_ok=True)
    return repo_workspace

def is_safe_path(basedir, path, follow_symlinks=True):
    basedir = os.path.realpath(basedir)
    if follow_symlinks:
        matchpath = os.path.realpath(path)
    else:
        matchpath = os.path.abspath(path)

    if os.path.commonpath([basedir, matchpath]) != basedir:
        return False

    # Prevent access to .git directory and its contents
    rel_path = os.path.relpath(matchpath, basedir)
    parts = rel_path.split(os.sep)
    if '.git' in parts:
        return False

    return True

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
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/setup-issue-fix', methods=['POST'])
def setup_issue_fix():
    g = get_github_client()
    token = session.get('github_token')
    if not g or not token:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    repo_full_name = data.get('repo_full_name')
    issue_number = data.get('issue_number')

    if not repo_full_name or not issue_number:
        return jsonify({"error": "repo_full_name and issue_number are required"}), 400

    repo_name = repo_full_name.split('/')[-1]
    workspace_dir = get_workspace_dir(repo_name)

    try:
        if not os.path.exists(os.path.join(workspace_dir, '.git')):
            # Clone if not exists
            auth_url = f"https://{token}@github.com/{repo_full_name}.git"
            repo = git.Repo.clone_from(auth_url, workspace_dir)
        else:
            repo = git.Repo(workspace_dir)

        # Update origin remote URL with token if needed
        origin = repo.remote('origin')
        if 'github.com' in origin.url:
            clean_url = re.sub(r'https://.*@github\.com/', 'https://github.com/', origin.url)
            auth_url = clean_url.replace('https://github.com/', f'https://{token}@github.com/')
            if auth_url != origin.url:
                origin.set_url(auth_url)

        origin.fetch()
        gh_repo = g.get_repo(repo_full_name)
        default_branch = gh_repo.default_branch
        fix_branch = f"fix/issue-{issue_number}"

        try:
            # Check if branch exists locally
            repo.git.checkout(fix_branch)
            msg = f"Switched to existing fix branch '{fix_branch}'"
        except git.GitCommandError:
            # Create from default branch
            repo.git.checkout('-B', fix_branch, f"origin/{default_branch}")
            msg = f"Created and checked out fix branch '{fix_branch}' from {default_branch}"

        session['active_repo'] = repo_name
        # Store active issue linkage in session
        if 'active_issues' not in session:
            session['active_issues'] = {}
        session['active_issues'][repo_name] = issue_number

        return jsonify({
            "message": msg,
            "branch": fix_branch,
            "path": workspace_dir
        }), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

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
            # Security: Validate paths before extraction to prevent Zip Slip
            for member in zip_ref.namelist():
                member_path = os.path.join(workspace_dir, member)
                if not is_safe_path(workspace_dir, member_path):
                    raise Exception(f"Potential Zip Slip detected: {member}")
            zip_ref.extractall(workspace_dir)

        os.remove(archive_path)
        session['active_repo'] = repo_name
        return jsonify({"message": "Repository downloaded and extracted successfully", "path": workspace_dir}), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

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
        return jsonify({"error": mask_token(str(e))}), 500

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
                # Manual check as first line of defense
                for member in tar_ref.getmembers():
                    member_path = os.path.join(full_target_dir, member.name)
                    if not is_safe_path(full_target_dir, member_path):
                        raise Exception(f"Potential Tar Slip detected: {member.name}")

                # Security: Use 'data' filter for extra protection if Python 3.12+
                try:
                    tar_ref.extractall(full_target_dir, filter='data')
                except TypeError:
                    tar_ref.extractall(full_target_dir)
        else:
            return jsonify({"error": "Unsupported archive format"}), 400

        os.remove(archive_path)
        return jsonify({"message": "Archive extracted successfully"}), 200
    except Exception as e:
        if os.path.exists(archive_path):
            os.remove(archive_path)
        return jsonify({"error": mask_token(str(e))}), 500

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
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/save-template', methods=['POST'])
def save_template():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    data = request.get_json() or request.form
    template_name = data.get('template_name')
    if not template_name:
        return jsonify({"error": "template_name is required"}), 400

    template_name = secure_filename(template_name)
    workspace_dir = get_workspace_dir(repo_name)

    # Use appdata/.zekiprod/templates as persistent storage
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    os.makedirs(templates_root, exist_ok=True)
    template_path = os.path.join(templates_root, template_name)

    if os.path.exists(template_path):
        shutil.rmtree(template_path)

    try:
        # Copy workspace content to template storage, excluding .git
        def ignore_git(path, names):
            return ['.git'] if '.git' in names else []

        shutil.copytree(workspace_dir, template_path, ignore=ignore_git)
        return jsonify({"message": f"Template '{template_name}' saved successfully"}), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/templates', methods=['GET'])
def list_templates():
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    if not os.path.exists(templates_root):
        return jsonify([]), 200

    templates = [d for d in os.listdir(templates_root) if os.path.isdir(os.path.join(templates_root, d))]
    return jsonify(templates), 200

@bp.route('/api/workspace/templates/<template_name>/manifest', methods=['GET'])
def get_manifest(template_name):
    template_name = secure_filename(template_name)
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    template_path = os.path.join(templates_root, template_name)

    if not os.path.exists(template_path):
        return jsonify({"error": "Template not found"}), 404

    manifest = get_template_manifest(template_path)
    if manifest:
        return jsonify(manifest), 200
    else:
        return jsonify({"variables": []}), 200

@bp.route('/api/workspace/templates/<template_name>', methods=['DELETE'])
def delete_template(template_name):
    template_name = secure_filename(template_name)
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    template_path = os.path.join(templates_root, template_name)

    if not os.path.exists(template_path):
        return jsonify({"error": "Template not found"}), 404

    try:
        shutil.rmtree(template_path)
        return jsonify({"message": f"Template '{template_name}' deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/files', methods=['GET'])
def list_workspace_files():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)

    def build_tree(path):
        tree = []
        try:
            for item in sorted(os.listdir(path)):
                if item == '.git':
                    continue
                full_path = os.path.join(path, item)

                # Security: Ensure path is safe (doesn't point outside workspace)
                # and explicitly avoid following symlinks during traversal to prevent leaks or loops.
                if not is_safe_path(workspace_dir, full_path, follow_symlinks=True):
                    continue

                rel_path = os.path.relpath(full_path, workspace_dir)
                is_symlink = os.path.islink(full_path)
                is_dir = os.path.isdir(full_path)

                node = {
                    "name": item,
                    "path": rel_path,
                    "type": "directory" if is_dir and not is_symlink else "file"
                }
                # Only recurse if it's a real directory, not a symlink, to prevent circularity or leaks
                if is_dir and not is_symlink:
                    node["children"] = build_tree(full_path)
                tree.append(node)
        except Exception:
            pass
        return tree

    return jsonify(build_tree(workspace_dir)), 200

@bp.route('/api/workspace/files', methods=['DELETE'])
def delete_workspace_file():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    data = request.get_json() or request.form
    target_rel_path = data.get('path')

    if not target_rel_path:
        return jsonify({"error": "Path is required"}), 400

    full_path = os.path.join(workspace_dir, target_rel_path)
    if not is_safe_path(workspace_dir, full_path):
        # Specific check for existing tests that expect 403 for .git
        rel_path = os.path.relpath(os.path.realpath(full_path), os.path.realpath(workspace_dir))
        parts = rel_path.split(os.sep)
        if '.git' in parts:
            return jsonify({"error": "Cannot access .git directory"}), 403
        return jsonify({"error": "Invalid path"}), 400

    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return jsonify({"message": f"Deleted {target_rel_path}"}), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/files/content', methods=['GET', 'POST'])
def get_file_content():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)

    if request.method == 'GET':
        target_rel_path = request.args.get('path')
    else:
        data = request.get_json() or request.form
        target_rel_path = data.get('path')

    if not target_rel_path:
        return jsonify({"error": "Path is required"}), 400

    full_path = os.path.join(workspace_dir, target_rel_path)
    if not is_safe_path(workspace_dir, full_path) or os.path.isdir(full_path):
        return jsonify({"error": "Invalid file path"}), 400

    if request.method == 'GET':
        # Limit file size to 1MB
        if os.path.exists(full_path) and os.path.getsize(full_path) > 1024 * 1024:
            return jsonify({"error": "File too large (max 1MB)"}), 400

        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return jsonify({"content": content, "path": target_rel_path}), 200
        except Exception as e:
            return jsonify({"error": mask_token(str(e))}), 500
    else:
        # POST - Save content
        data = request.get_json() or request.form
        content = data.get('content')
        if content is None:
            return jsonify({"error": "content is required"}), 400

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return jsonify({"message": f"File {target_rel_path} saved successfully"}), 200
        except Exception as e:
            return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/apply-template', methods=['POST'])
def apply_template():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    data = request.get_json() or request.form
    template_name = data.get('template_name')
    context = data.get('context', {})
    if isinstance(context, str):
        try:
            import json
            context = json.loads(context)
        except Exception:
            context = {}

    if not template_name:
        return jsonify({"error": "template_name is required"}), 400

    template_name = secure_filename(template_name)
    workspace_dir = get_workspace_dir(repo_name)
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    template_path = os.path.join(templates_root, template_name)

    if not os.path.exists(template_path):
        return jsonify({"error": "Template not found"}), 404

    try:
        # Use render_template_dir for dynamic scaffolding
        render_template_dir(template_path, workspace_dir, context, is_safe_path, workspace_dir)
        return jsonify({"message": f"Template '{template_name}' applied to workspace"}), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/import-template', methods=['POST'])
def import_template():
    token = session.get('github_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    repo_url = data.get('repo_url')
    template_name = data.get('template_name')

    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    if not template_name:
        template_name = repo_url.split('/')[-1].replace('.git', '')

    template_name = secure_filename(template_name)
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    template_path = os.path.join(templates_root, template_name)

    if os.path.exists(template_path):
        shutil.rmtree(template_path)

    try:
        if repo_url.startswith('https://github.com/'):
            auth_url = repo_url.replace('https://github.com/', f'https://{token}@github.com/')
        else:
            auth_url = repo_url

        # Clone to a temporary directory first to remove .git
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            git.Repo.clone_from(auth_url, tmp_dir, depth=1)
            shutil.rmtree(os.path.join(tmp_dir, '.git'))
            shutil.copytree(tmp_dir, template_path)

        return jsonify({"message": f"Repository imported as template '{template_name}'"}), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/activate', methods=['POST'])
def activate_workspace():
    data = request.get_json() or request.form
    repo_name = data.get('repo_name')
    if not repo_name:
        return jsonify({"error": "repo_name is required"}), 400

    session['active_repo'] = repo_name
    return jsonify({"message": f"Workspace '{repo_name}' activated"}), 200

@bp.route('/api/workspace/portfolio', methods=['GET'])
def workspace_portfolio():
    session_id = secure_filename(session.get('session_id', 'default'))
    workspace_root = os.path.join('/tmp/gh-web-workspaces', session_id)

    if not os.path.exists(workspace_root):
        return jsonify([]), 200

    portfolio = []
    try:
        for repo_dir in sorted(os.listdir(workspace_root)):
            repo_path = os.path.join(workspace_root, repo_dir)
            if not os.path.isdir(repo_path):
                continue

            git_path = os.path.join(repo_path, '.git')
            if not os.path.exists(git_path):
                continue

            try:
                repo = git.Repo(repo_path)

                # Try to resolve full name from remote URL
                full_name = None
                try:
                    url = repo.remotes.origin.url
                    match = re.search(r'github\.com[:/](.+?)(?:\.git)?$', url)
                    if match:
                        full_name = match.group(1)
                except Exception:
                    pass

                portfolio.append({
                    "repo_name": repo_dir,
                    "full_name": full_name,
                    "branch": repo.active_branch.name,
                    "is_dirty": repo.is_dirty(),
                    "untracked": len(repo.untracked_files) > 0
                })
            except Exception:
                # Skip invalid repos
                continue

        return jsonify(portfolio), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/status', methods=['GET'])
def workspace_status():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    if not os.path.exists(os.path.join(workspace_dir, '.git')):
        return jsonify({"is_git": False}), 200

    try:
        repo = git.Repo(workspace_dir)
        can_push = False

        # Check if we can push to the tracking remote
        tracking = None
        try:
            tracking = repo.active_branch.tracking_branch()
        except Exception:
            pass

        if tracking:
            remote = repo.remote(tracking.remote_name)
            url = remote.url
            if 'github.com' in url:
                # Extract repo full name from URL
                match = re.search(r'github\.com[:/](.+?)(?:\.git)?$', url)
                if match:
                    repo_full_name = match.group(1)
                    g = get_github_client()
                    if g:
                        try:
                            gh_repo = g.get_repo(repo_full_name)
                            can_push = gh_repo.permissions.push
                        except Exception:
                            pass

        # Check for active issue linkage
        active_issue = session.get('active_issues', {}).get(repo_name)

        return jsonify({
            "is_git": True,
            "branch": repo.active_branch.name,
            "is_dirty": repo.is_dirty(),
            "untracked": len(repo.untracked_files) > 0,
            "can_push": can_push,
            "active_issue": active_issue
        }), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/branch', methods=['POST'])
def workspace_branch():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    if not os.path.exists(os.path.join(workspace_dir, '.git')):
        return jsonify({"error": "Not a git repository"}), 400

    data = request.get_json() or request.form
    branch_name = data.get('branch_name')
    create_new = data.get('create_new') in [True, 'true', 'on', '1']

    if not branch_name:
        return jsonify({"error": "branch_name is required"}), 400

    try:
        repo = git.Repo(workspace_dir)
        if create_new:
            repo.git.checkout('-b', branch_name)
            msg = f"Branch '{branch_name}' created and checked out"
        else:
            repo.git.checkout(branch_name)
            msg = f"Switched to branch '{branch_name}'"

        return jsonify({"message": msg, "branch": branch_name}), 200
    except Exception as e:
        return jsonify({"error": mask_token(f"Failed to change branch: {str(e)}")}), 500

@bp.route('/api/workspace/push', methods=['POST'])
def workspace_push():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    if not os.path.exists(os.path.join(workspace_dir, '.git')):
        return jsonify({"error": "Not a git repository"}), 400

    token = session.get('github_token')
    if not token:
         return jsonify({"error": "Unauthorized"}), 401

    try:
        repo = git.Repo(workspace_dir)

        # Determine target remote from tracking branch
        tracking = repo.active_branch.tracking_branch()
        remote_name = 'origin'
        if tracking:
            remote_name = tracking.remote_name

        target_remote = repo.remote(remote_name)
        url = target_remote.url

        # Always update URL with current session token if it's a GitHub URL
        if 'github.com' in url:
            # Remove existing token if present and inject current one
            clean_url = re.sub(r'https://.*@github\.com/', 'https://github.com/', url)
            auth_url = clean_url.replace('https://github.com/', f'https://{token}@github.com/')
            if auth_url != url:
                target_remote.set_url(auth_url)

        # Use explicit refspec to push local branch to correct remote branch
        refspec = repo.active_branch.name
        if tracking:
            refspec = f"{repo.active_branch.name}:{tracking.remote_head}"

        target_remote.push(refspec)
        return jsonify({"message": f"Pushed branch '{repo.active_branch.name}' to {remote_name} as '{tracking.remote_head if tracking else repo.active_branch.name}'"}), 200
    except Exception as e:
        return jsonify({"error": mask_token(f"Failed to push to remote: {str(e)}")}), 500

@bp.route('/api/workspace/diff', methods=['GET'])
def workspace_diff():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    if not os.path.exists(os.path.join(workspace_dir, '.git')):
        return jsonify({"error": "Active workspace is not a git repository"}), 400

    try:
        repo = git.Repo(workspace_dir)
        try:
            # Check if there are any commits
            repo.head.commit
            # Diff against HEAD to see both staged and unstaged changes
            diff_text = repo.git.diff('HEAD')
        except (ValueError, git.GitCommandError):
            # No commits yet, diff against empty tree to show all changes (including staged)
            try:
                # Use magic hash for empty tree: 4b825dc642cb6eb9a060e54bf8d69288fbee4904
                diff_text = repo.git.diff('4b825dc642cb6eb9a060e54bf8d69288fbee4904')
            except git.GitCommandError:
                # Fallback to simple diff if that fails
                diff_text = repo.git.diff()

        return jsonify({"diff": diff_text}), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/history', methods=['GET'])
def workspace_history():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    if not os.path.exists(os.path.join(workspace_dir, '.git')):
        return jsonify({"error": "Active workspace is not a git repository"}), 400

    try:
        repo = git.Repo(workspace_dir)
        commits = []
        try:
            # Limit to last 50 commits
            for commit in repo.iter_commits(max_count=50):
                commits.append({
                    "hash": commit.hexsha,
                    "author": commit.author.name,
                    "date": commit.authored_datetime.isoformat(),
                    "message": commit.message.strip()
                })
        except git.GitCommandError:
            # Likely no commits yet
            pass

        return jsonify(commits), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/stream-pr', methods=['POST'])
def stream_pr():
    g = get_github_client()
    token = session.get('github_token')
    if not g or not token:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    repo_full_name = data.get('repo_full_name')
    pr_number = data.get('pr_number')

    if not repo_full_name or not pr_number:
        return jsonify({"error": "repo_full_name and pr_number are required"}), 400

    repo_name = repo_full_name.split('/')[-1]
    workspace_dir = get_workspace_dir(repo_name)

    try:
        if not os.path.exists(os.path.join(workspace_dir, '.git')):
            # Clone if not exists
            auth_url = f"https://{token}@github.com/{repo_full_name}.git"
            repo = git.Repo.clone_from(auth_url, workspace_dir)
        else:
            repo = git.Repo(workspace_dir)

        # Update origin remote URL with token if needed
        origin = repo.remote('origin')
        if 'github.com' in origin.url:
            clean_url = re.sub(r'https://.*@github\.com/', 'https://github.com/', origin.url)
            auth_url = clean_url.replace('https://github.com/', f'https://{token}@github.com/')
            if auth_url != origin.url:
                origin.set_url(auth_url)

        # Fetch detailed PR info for collaboration support
        gh_repo = g.get_repo(repo_full_name)
        pr = gh_repo.get_pull(int(pr_number))

        local_branch = f"review-pr-{pr_number}"
        head_repo_full_name = pr.head.repo.full_name if pr.head.repo else None
        head_ref = pr.head.ref

        if head_repo_full_name and head_repo_full_name != repo_full_name:
            # PR is from a fork
            remote_name = 'head-fork'
            auth_fork_url = f"https://{token}@github.com/{head_repo_full_name}.git"

            try:
                fork_remote = repo.remote(remote_name)
                fork_remote.set_url(auth_fork_url)
            except (ValueError, git.GitCommandError, IndexError):
                fork_remote = repo.create_remote(remote_name, auth_fork_url)

            fork_remote.fetch()
            # Create/Reset local branch to track fork branch
            repo.git.checkout('-B', local_branch, f"{remote_name}/{head_ref}")
            repo.git.branch("--set-upstream-to", f"{remote_name}/{head_ref}", local_branch)
            msg = f"PR #{pr_number} from fork {head_repo_full_name} is now active in workspace (Collaborative Mode)"
        else:
            # PR is from the same repo
            origin.fetch()
            repo.git.checkout('-B', local_branch, f"origin/{head_ref}")
            repo.git.branch("--set-upstream-to", f"origin/{head_ref}", local_branch)
            msg = f"PR #{pr_number} from {repo_full_name} is now active in workspace"

        session['active_repo'] = repo_name
        return jsonify({
            "message": msg,
            "branch": local_branch,
            "path": workspace_dir
        }), 200
    except Exception as e:
        # Fallback to read-only PR ref if branch-based checkout fails
        try:
            repo = git.Repo(workspace_dir)
            pr_ref = f"pull/{pr_number}/head"
            local_branch = f"review-pr-{pr_number}"
            repo.remotes.origin.fetch(f"{pr_ref}:{local_branch}", force=True)
            repo.git.checkout(local_branch, force=True)
            session['active_repo'] = repo_name
            return jsonify({
                "message": f"PR #{pr_number} is active (Read-Only fallback)",
                "branch": local_branch,
                "path": workspace_dir
            }), 200
        except Exception as fallback_err:
            return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/sync', methods=['POST'])
def workspace_sync():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    if not os.path.exists(os.path.join(workspace_dir, '.git')):
        return jsonify({"error": "Active workspace is not a git repository"}), 400

    try:
        repo = git.Repo(workspace_dir)
        # Fetch from all remotes to ensure we're up to date
        for remote in repo.remotes:
            remote.fetch()
        return jsonify({"message": "Workspace synced with remote successfully"}), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/revert', methods=['POST'])
def workspace_revert():
    repo_name = session.get('active_repo')
    if not repo_name:
        return jsonify({"error": "No active repository in workspace"}), 400

    workspace_dir = get_workspace_dir(repo_name)
    if not os.path.exists(os.path.join(workspace_dir, '.git')):
        return jsonify({"error": "Active workspace is not a git repository"}), 400

    try:
        repo = git.Repo(workspace_dir)
        try:
            # Hard reset to HEAD if commits exist
            repo.head.commit
            repo.git.reset('--hard', 'HEAD')
        except (ValueError, git.GitCommandError):
            # No commits yet, just clear the index and delete all files except .git
            repo.git.rm('-r', '--cached', '.', ignore_unmatch=True)
            for item in os.listdir(workspace_dir):
                if item == '.git': continue
                item_path = os.path.join(workspace_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

        repo.git.clean('-fd')
        return jsonify({"message": "Workspace changes discarded successfully"}), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
