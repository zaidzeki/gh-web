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

@patch('app.workspace.routes.get_github_client')
@patch('git.Repo.clone_from')
@patch('git.Repo')
def test_stream_pr_to_workspace(mock_repo_class, mock_clone, mock_get_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'

    # Mock github client
    mock_gh = MagicMock()
    mock_get_github.return_value = mock_gh
    mock_gh_repo = MagicMock()
    mock_gh.get_repo.return_value = mock_gh_repo
    mock_pr = MagicMock()
    mock_gh_repo.get_pull.return_value = mock_pr
    mock_pr.head.repo.full_name = 'owner/repo'
    mock_pr.head.ref = 'feature-branch'

    # Mock git repo
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.branches = []
    mock_clone.return_value = mock_repo

    # Mock remote and origin
    mock_origin = MagicMock()
    mock_origin.url = "https://github.com/owner/repo.git"
    mock_repo.remote.return_value = mock_origin
    mock_repo.remotes.origin = mock_origin

    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False # Force clone

        response = client.post('/api/workspace/stream-pr', json={
            'repo_full_name': 'owner/repo',
            'pr_number': '123'
        })

    assert response.status_code == 200
    data = response.get_json()
    assert "PR #123 from owner/repo is now active in workspace" in data['message']
    assert data['branch'] == "review-pr-123"

    mock_clone.assert_called_once()
    mock_origin.fetch.assert_called_once()
    mock_repo.git.checkout.assert_called_with('-B', 'review-pr-123', 'origin/feature-branch')

@patch('app.workspace.routes.get_github_client')
@patch('git.Repo.clone_from')
@patch('git.Repo')
def test_stream_pr_collaborative_mode(mock_repo_class, mock_clone, mock_get_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'

    # Mock github client
    mock_gh = MagicMock()
    mock_get_github.return_value = mock_gh
    mock_gh_repo = MagicMock()
    mock_gh.get_repo.return_value = mock_gh_repo
    mock_pr = MagicMock()
    mock_gh_repo.get_pull.return_value = mock_pr
    mock_pr.head.repo.full_name = 'fork-owner/repo'
    mock_pr.head.ref = 'fix-branch'

    # Mock git repo
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.branches = []
    mock_clone.return_value = mock_repo

    # Mock remote and origin
    mock_origin = MagicMock()
    mock_origin.url = "https://github.com/owner/repo.git"

    def mock_remote_side_effect(name):
        if name == 'origin':
            return mock_origin
        raise ValueError("Remote not found")

    mock_repo.remote.side_effect = mock_remote_side_effect
    mock_repo.remotes.origin = mock_origin

    mock_fork_remote = MagicMock()
    mock_repo.create_remote.return_value = mock_fork_remote

    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True # Already cloned

        response = client.post('/api/workspace/stream-pr', json={
            'repo_full_name': 'owner/repo',
            'pr_number': '456'
        })

    assert response.status_code == 200
    data = response.get_json()
    assert "Collaborative Mode" in data['message']
    assert "fork-owner/repo" in data['message']

    mock_repo.create_remote.assert_called_with('head-fork', 'https://fake_token@github.com/fork-owner/repo.git')
    mock_fork_remote.fetch.assert_called_once()
    mock_repo.git.checkout.assert_called_with('-B', 'review-pr-456', 'head-fork/fix-branch')

def test_stream_pr_missing_params(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    response = client.post('/api/workspace/stream-pr', json={})
    assert response.status_code == 400
    assert "repo_full_name and pr_number are required" in response.get_json()['error']

def test_stream_pr_unauthorized(client):
    response = client.post('/api/workspace/stream-pr', json={
        'repo_full_name': 'owner/repo',
        'pr_number': '123'
    })
    assert response.status_code == 401
