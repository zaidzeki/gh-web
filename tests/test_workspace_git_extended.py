import pytest
from unittest.mock import MagicMock, patch
from app import create_app
import os

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

@patch('git.Repo')
def test_workspace_status(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'

    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)

    mock_repo = MagicMock()
    mock_repo.active_branch.name = 'main'
    mock_repo.is_dirty.return_value = True
    mock_repo.untracked_files = ['new.txt']
    mock_repo_class.return_value = mock_repo

    response = client.get('/api/workspace/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['is_git'] is True
    assert data['branch'] == 'main'
    assert data['is_dirty'] is True
    assert data['untracked'] is True

@patch('git.Repo')
def test_workspace_branch_switch(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'

    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    response = client.post('/api/workspace/branch', json={'branch_name': 'feat/ui'})
    assert response.status_code == 200
    assert "Switched to branch 'feat/ui'" in response.get_json()['message']
    mock_repo.git.checkout.assert_called_with('feat/ui')

@patch('git.Repo')
def test_workspace_branch_create(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'

    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    response = client.post('/api/workspace/branch', json={'branch_name': 'new-branch', 'create_new': True})
    assert response.status_code == 200
    assert "Branch 'new-branch' created" in response.get_json()['message']
    mock_repo.git.checkout.assert_called_with('-b', 'new-branch')

@patch('git.Repo')
def test_workspace_push(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'
        sess['github_token'] = 'fake_token'

    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)

    mock_repo = MagicMock()
    mock_repo.active_branch.name = 'main'
    mock_remote = MagicMock()
    mock_remote.url = 'https://github.com/owner/repo.git'
    mock_repo.remote.return_value = mock_remote
    mock_repo_class.return_value = mock_repo

    response = client.post('/api/workspace/push')
    assert response.status_code == 200
    assert "Pushed branch 'main' to origin" in response.get_json()['message']
    mock_remote.set_url.assert_called_with('https://fake_token@github.com/owner/repo.git')
    mock_remote.push.assert_called_with('main')
