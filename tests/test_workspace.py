import pytest
from unittest.mock import MagicMock, patch
from app import create_app
import os
import io
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

@patch('git.Repo.clone_from')
def test_clone_repo(mock_clone, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'

    response = client.post('/api/workspace/clone', json={'repo_url': 'https://github.com/owner/repo.git'})
    assert response.status_code == 201
    assert "Repository cloned successfully" in response.get_json()['message']
    mock_clone.assert_called_once()

@patch('app.workspace.routes.Github')
@patch('httpx.stream')
@patch('zipfile.ZipFile')
def test_download_repo(mock_zip, mock_stream, mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'

    mock_repo = MagicMock()
    mock_repo.get_archive_link.return_value = "http://example.com/archive.zip"
    mock_github.return_value.get_repo.return_value = mock_repo

    mock_response = MagicMock()
    mock_response.iter_bytes.return_value = [b'data']
    mock_stream.return_value.__enter__.return_value = mock_response

    mock_zip_instance = MagicMock()
    mock_zip.return_value.__enter__.return_value = mock_zip_instance

    response = client.post('/api/workspace/download', json={'repo_name': 'owner/repo', 'ref': 'main'})
    assert response.status_code == 201
    assert "Repository downloaded and extracted successfully" in response.get_json()['message']

def test_upload_file(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    data = {
        'file': (io.BytesIO(b"hello world"), 'test.txt'),
        'target_path': 'subdir'
    }
    response = client.post('/api/workspace/modify/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert "uploaded successfully" in response.get_json()['message']
    assert os.path.exists('/tmp/gh-web-workspaces/test_session/testrepo/subdir/test.txt')

@patch('git.Repo')
def test_commit_changes(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    response = client.post('/api/workspace/commit', json={'commit_message': 'feat: test'})
    assert response.status_code == 200
    assert "committed successfully" in response.get_json()['message']
    mock_repo.git.add.assert_called_with(all=True)
    mock_repo.index.commit.assert_called_with('feat: test')

@patch('git.Repo')
def test_workspace_status_pr_context(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'
        sess['active_issues'] = {
            'testrepo': {
                'number': 123,
                'title': 'Test PR',
                'default_branch': 'main',
                'repo_full_name': 'owner/repo',
                'is_pr': True
            }
        }

    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.active_branch.name = 'review-pr-123'
    mock_repo.is_dirty.return_value = False
    mock_repo.untracked_files = []

    response = client.get('/api/workspace/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['active_issue'] == 123
    assert data['is_pr'] is True
    assert data['repo_full_name'] == 'owner/repo'
