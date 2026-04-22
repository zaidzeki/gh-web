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

@patch('git.Repo.clone_from')
@patch('git.Repo')
def test_stream_pr_to_workspace(mock_repo_class, mock_clone, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'

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
    mock_origin.fetch.assert_called_once_with("pull/123/head:review-pr-123", force=True)
    mock_repo.git.checkout.assert_called_with("review-pr-123", force=True)

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
