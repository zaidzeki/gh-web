import pytest
from app import create_app
import os
import shutil

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
        'SESSION_COOKIE_SECURE': False
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_delete_workspace_root_prevention(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['active_repo'] = 'test-repo'
        sess['session_id'] = 'test-session'

    # Ensure workspace exists
    workspace_dir = '/tmp/gh-web-workspaces/test-session/test-repo'
    os.makedirs(workspace_dir, exist_ok=True)
    test_file = os.path.join(workspace_dir, 'keep-me.txt')
    with open(test_file, 'w') as f:
        f.write('should not be deleted')

    try:
        # Try to delete root '.'
        response = client.delete('/api/workspace/files', json={'path': '.'})
        assert response.status_code == 400
        assert b'Cannot delete workspace root' in response.data
        assert os.path.exists(test_file)

        # Try to delete root '' (which is caught by 'Path is required' check first)
        response = client.delete('/api/workspace/files', json={'path': ''})
        assert response.status_code == 400
        assert b'Path is required' in response.data
        assert os.path.exists(test_file)

        # Try to delete root '/'
        response = client.delete('/api/workspace/files', json={'path': '/'})
        assert response.status_code == 400
        assert b'Cannot delete workspace root' in response.data
        assert os.path.exists(test_file)

    finally:
        if os.path.exists('/tmp/gh-web-workspaces/test-session'):
            shutil.rmtree('/tmp/gh-web-workspaces/test-session')
