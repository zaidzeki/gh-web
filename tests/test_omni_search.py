import os
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-key'
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_session(app):
    with app.test_request_context():
        with patch('app.workspace.routes.session', dict()) as sess:
            sess['github_token'] = 'test-token'
            sess['active_repo'] = 'test-repo'
            sess['session_id'] = 'test-session'
            yield sess

def test_search_requires_auth(client):
    response = client.get('/api/workspace/search?q=test')
    assert response.status_code == 400 # No active repo

def test_search_requires_query(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['active_repo'] = 'test-repo'

    response = client.get('/api/workspace/search')
    assert response.status_code == 400
    assert b"Search query 'q' is required" in response.data

@patch('app.workspace.routes.subprocess.run')
@patch('app.workspace.routes.get_workspace_dir')
@patch('app.workspace.routes.is_safe_path')
def test_search_success(mock_is_safe, mock_get_dir, mock_run, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['active_repo'] = 'test-repo'

    workspace_dir = '/tmp/test-repo'
    mock_get_dir.return_value = workspace_dir
    mock_is_safe.return_value = True

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=f"{workspace_dir}/file.txt:10:found content\n",
        stderr=""
    )

    response = client.get('/api/workspace/search?q=found')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['path'] == 'file.txt'
    assert data[0]['line'] == '10'
    assert data[0]['content'] == 'found content'

@patch('app.workspace.routes.subprocess.run')
@patch('app.workspace.routes.get_workspace_dir')
@patch('app.workspace.routes.is_safe_path')
def test_search_security_filtering(mock_is_safe, mock_get_dir, mock_run, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['active_repo'] = 'test-repo'

    workspace_dir = '/tmp/test-repo'
    mock_get_dir.return_value = workspace_dir

    # Mock one safe and one unsafe path
    def is_safe(basedir, path):
        return '.git' not in path

    mock_is_safe.side_effect = is_safe

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=f"{workspace_dir}/safe.txt:1:ok\n{workspace_dir}/.git/config:1:secret\n",
        stderr=""
    )

    response = client.get('/api/workspace/search?q=test')
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['path'] == 'safe.txt'
