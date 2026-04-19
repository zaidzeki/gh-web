import os
import shutil
import git
import tempfile
from flask import Blueprint, request, session, jsonify
from github import Github
from werkzeug.utils import secure_filename

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

    template_name = data.get('template_name')
    if template_name:
        template_name = secure_filename(template_name)

    try:
        user = g.get_user()
        repo = user.create_repo(
            name,
            description=description,
            private=private
        )

        if template_name:
            templates_root = os.path.expanduser('~/.zekiprod/templates')
            template_path = os.path.join(templates_root, template_name)

            if os.path.exists(template_path):
                # Temporary directory for cloning and initializing
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Clone the new repository
                    auth_url = repo.clone_url.replace('https://github.com/', f'https://{session["github_token"]}@github.com/')
                    local_repo = git.Repo.clone_from(auth_url, tmp_dir)

                    # Copy template content to the repo
                    for item in os.listdir(template_path):
                        s = os.path.join(template_path, item)
                        d = os.path.join(tmp_dir, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy(s, d)

                    # Configure Git identity
                    with local_repo.config_writer() as cw:
                        cw.set_value("user", "name", "GH-Web User")
                        cw.set_value("user", "email", "gh-web@example.com")

                    # Commit and push
                    local_repo.git.add(A=True)
                    local_repo.index.commit("Initial commit from template")
                    local_repo.git.push('origin', 'main')

        return jsonify({
            "message": f"Repository {name} created successfully" + (" with template" if template_name else ""),
            "full_name": repo.full_name,
            "clone_url": repo.clone_url
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
