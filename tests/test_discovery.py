import pytest
from app import create_app
from unittest.mock import MagicMock, patch
import json

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_get_user_profile(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.auth.routes.get_github_client') as mock_github:
        mock_user = MagicMock()
        mock_user.login = 'testuser'
        mock_user.avatar_url = 'http://avatar.url'
        mock_user.name = 'Test User'
        mock_user.html_url = 'http://github.com/testuser'
        mock_github.return_value.get_user.return_value = mock_user

        response = client.get('/api/user')
        assert response.status_code == 200
        data = response.get_json()
        assert data['login'] == 'testuser'
        assert data['avatar_url'] == 'http://avatar.url'

def test_list_repos(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.repos.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_repo.full_name = 'owner/repo'
        mock_repo.name = 'repo'
        mock_repo.description = 'desc'
        mock_repo.html_url = 'http://github.com/owner/repo'
        mock_repo.stargazers_count = 10
        mock_repo.open_issues_count = 5
        mock_repo.pushed_at = None
        mock_repo.private = False

        mock_github.return_value.get_user.return_value.get_repos.return_value = [mock_repo]

        response = client.get('/api/repos')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['full_name'] == 'owner/repo'

def test_workspace_portfolio(client):
    with client.session_transaction() as sess:
        sess['session_id'] = 'test-session'

    import os
    import shutil
    workspace_root = '/tmp/gh-web-workspaces/test-session'
    repo_path = os.path.join(workspace_root, 'test-repo')
    os.makedirs(os.path.join(repo_path, '.git'), exist_ok=True)

    with patch('git.Repo') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.active_branch.name = 'main'
        mock_repo.is_dirty.return_value = False
        mock_repo.untracked_files = []
        mock_repo.remotes.origin.url = 'https://github.com/owner/test-repo.git'
        mock_repo_class.return_value = mock_repo

        response = client.get('/api/workspace/portfolio')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['repo_name'] == 'test-repo'
        assert data[0]['branch'] == 'main'

    shutil.rmtree(workspace_root)

def test_activate_workspace(client):
    response = client.post('/api/workspace/activate', json={'repo_name': 'test-repo'})
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess['active_repo'] == 'test-repo'
