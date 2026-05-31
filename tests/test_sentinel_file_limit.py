import pytest
import os
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

def test_save_file_limit(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session_limit'
        sess['active_repo'] = 'limitrepo'

    workspace_dir = '/tmp/gh-web-workspaces/test_session_limit/limitrepo'
    os.makedirs(workspace_dir, exist_ok=True)

    file_path = 'test_limit.txt'
    full_path = os.path.join(workspace_dir, file_path)

    # 1. Test saving a small file (under 1MB) - should succeed
    small_content = "a" * 1024 # 1KB
    response = client.post('/api/workspace/files/content', json={
        'path': file_path,
        'content': small_content
    })
    assert response.status_code == 200
    assert "saved successfully" in response.get_json()['message']

    # 2. Test saving a large file (over 1MB) - should fail with 400
    large_content = "a" * (1024 * 1024 + 1) # 1MB + 1 byte
    response = client.post('/api/workspace/files/content', json={
        'path': file_path,
        'content': large_content
    })

    # This assertion is expected to FAIL before the fix
    assert response.status_code == 400
    assert "File too large" in response.get_json()['error']
