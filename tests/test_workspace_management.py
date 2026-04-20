import pytest
import os
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

def test_list_workspace_files(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    workspace_dir = '/tmp/gh-web-workspaces/test_session/testrepo'
    os.makedirs(workspace_dir, exist_ok=True)
    with open(os.path.join(workspace_dir, 'file1.txt'), 'w') as f:
        f.write("content1")
    os.makedirs(os.path.join(workspace_dir, 'subdir'), exist_ok=True)
    with open(os.path.join(workspace_dir, 'subdir/file2.txt'), 'w') as f:
        f.write("content2")

    response = client.get('/api/workspace/files')
    assert response.status_code == 200
    data = response.get_json()

    # Verify structure
    names = [node['name'] for node in data]
    assert 'file1.txt' in names
    assert 'subdir' in names

    subdir = next(node for node in data if node['name'] == 'subdir')
    assert subdir['type'] == 'directory'
    assert subdir['children'][0]['name'] == 'file2.txt'

def test_get_file_content(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    workspace_dir = '/tmp/gh-web-workspaces/test_session/testrepo'
    os.makedirs(workspace_dir, exist_ok=True)
    with open(os.path.join(workspace_dir, 'test.txt'), 'w') as f:
        f.write("hello atlas")

    response = client.get('/api/workspace/files/content?path=test.txt')
    assert response.status_code == 200
    assert response.get_json()['content'] == "hello atlas"

def test_delete_workspace_file(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    workspace_dir = '/tmp/gh-web-workspaces/test_session/testrepo'
    file_path = os.path.join(workspace_dir, 'to_delete.txt')
    with open(file_path, 'w') as f:
        f.write("delete me")

    response = client.delete('/api/workspace/files', json={'path': 'to_delete.txt'})
    assert response.status_code == 200
    assert not os.path.exists(file_path)

def test_delete_git_fails(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    response = client.delete('/api/workspace/files', json={'path': '.git'})
    assert response.status_code == 403
