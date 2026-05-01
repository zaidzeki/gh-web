import os
import pytest
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

def test_security_headers(client):
    response = client.get('/')
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    csp = response.headers['Content-Security-Policy']
    assert "frame-ancestors 'none'" in csp
    assert "form-action 'self'" in csp

def test_workspace_directory_permissions(client):
    session_id = "perm-test-session"
    repo_name = "perm-test-repo"

    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'
        sess['session_id'] = session_id
        sess['active_repo'] = repo_name

    # Trigger directory creation
    client.get('/api/workspace/files')

    base_dir = '/tmp/gh-web-workspaces'
    session_dir = os.path.join(base_dir, session_id)
    repo_dir = os.path.join(session_dir, repo_name)

    # Check permissions (only owner should have access: 0700)
    assert os.path.exists(base_dir)
    assert oct(os.stat(base_dir).st_mode & 0o777) == '0o700'
    assert os.path.exists(repo_dir)
    assert oct(os.stat(repo_dir).st_mode & 0o777) == '0o700'
