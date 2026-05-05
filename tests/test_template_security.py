import os
import pytest
import shutil
from app import create_app

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_template_directory_permissions(client, mocker):
    # Mock os.path.expanduser to use a temporary directory instead of the real home directory
    import tempfile
    test_dir = tempfile.mkdtemp()
    mocker.patch('os.path.expanduser', side_effect=lambda x: x.replace('~', test_dir))

    templates_root = os.path.join(test_dir, '.zekiprod/templates')
    root_dir = os.path.join(test_dir, '.zekiprod')

    # Use a dummy repo in /tmp for testing save-template
    session_id = "test-session"
    repo_name = "test-repo"
    workspace_dir = f"/tmp/gh-web-workspaces/{session_id}/{repo_name}"
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    os.makedirs(workspace_dir)

    try:
        with client.session_transaction() as sess:
            sess['github_token'] = 'fake-token'
            sess['active_repo'] = repo_name
            sess['session_id'] = session_id

        # Trigger save_template via API
        response = client.post('/api/workspace/save-template', json={'template_name': 'test-template'})
        assert response.status_code == 201

        # Verify permissions of ~/.zekiprod and ~/.zekiprod/templates
        assert os.path.exists(root_dir)
        assert os.path.exists(templates_root)

        root_mode = os.stat(root_dir).st_mode & 0o777
        templates_mode = os.stat(templates_root).st_mode & 0o777

        assert root_mode == 0o700, f"Root directory {root_dir} has insecure permissions: {oct(root_mode)}"
        assert templates_mode == 0o700, f"Templates directory {templates_root} has insecure permissions: {oct(templates_mode)}"

    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        if os.path.exists(f"/tmp/gh-web-workspaces/{session_id}"):
            shutil.rmtree(f"/tmp/gh-web-workspaces/{session_id}")
