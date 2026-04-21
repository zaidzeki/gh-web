import pytest
from unittest.mock import MagicMock, patch
from app import create_app
import os
import shutil

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

def test_apply_template_to_workspace(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'

    workspace_dir = '/tmp/gh-web-workspaces/test_session/testrepo'
    os.makedirs(workspace_dir, exist_ok=True)

    # Existing file
    with open(os.path.join(workspace_dir, 'keep.txt'), 'w') as f:
        f.write("stay")

    # Prepare template
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    template_path = os.path.join(templates_root, 'merge-template')
    os.makedirs(template_path, exist_ok=True)
    with open(os.path.join(template_path, 'new.txt'), 'w') as f:
        f.write("merged")

    response = client.post('/api/workspace/apply-template', json={'template_name': 'merge-template'})
    assert response.status_code == 200
    assert "applied to workspace" in response.get_json()['message']

    assert os.path.exists(os.path.join(workspace_dir, 'keep.txt'))
    assert os.path.exists(os.path.join(workspace_dir, 'new.txt'))

def test_edit_file_content(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'

    workspace_dir = '/tmp/gh-web-workspaces/test_session/testrepo'
    os.makedirs(workspace_dir, exist_ok=True)
    file_path = os.path.join(workspace_dir, 'edit.txt')
    with open(file_path, 'w') as f:
        f.write("original")

    # Test GET
    response = client.get('/api/workspace/files/content?path=edit.txt')
    assert response.status_code == 200
    assert response.get_json()['content'] == "original"

    # Test POST
    response = client.post('/api/workspace/files/content', json={
        'path': 'edit.txt',
        'content': 'modified content'
    })
    assert response.status_code == 200
    assert "saved successfully" in response.get_json()['message']

    with open(file_path, 'r') as f:
        assert f.read() == "modified content"

@patch('git.Repo.clone_from')
def test_import_template_from_remote(mock_clone, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_clone.return_value = mock_repo

    # We need to mock the filesystem operations inside import_template because it uses a tempdir
    with patch('shutil.copytree'), patch('shutil.rmtree'):
        response = client.post('/api/workspace/import-template', json={
            'repo_url': 'https://github.com/owner/cool-repo',
            'template_name': 'imported-template'
        })

    assert response.status_code == 201
    assert "imported as template 'imported-template'" in response.get_json()['message']
    mock_clone.assert_called_once()
