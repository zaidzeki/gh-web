import pytest
from unittest.mock import MagicMock, patch
import os
import datetime

@pytest.fixture
def client():
    from app import create_app
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

@patch('app.milestones.routes.Github')
@patch('git.Repo')
@patch('os.path.exists')
@patch('os.path.isdir')
@patch('os.listdir')
def test_workspace_portfolio_milestones_success(mock_listdir, mock_isdir, mock_exists, mock_repo, mock_github, client):
    # Setup session
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'
        sess['session_id'] = 'test-session'

    # Mock filesystem
    mock_exists.return_value = True
    mock_isdir.return_value = True
    mock_listdir.return_value = ['repo1']

    # Mock GitRepo
    mock_repo_instance = MagicMock()
    mock_repo.return_value = mock_repo_instance
    mock_origin = MagicMock()
    mock_origin.url = 'https://github.com/owner/repo1.git'
    mock_repo_instance.remotes.origin = mock_origin
    mock_repo_instance.remotes.__contains__.return_value = True

    # Mock GitHub API
    mock_gh_instance = MagicMock()
    mock_github.return_value = mock_gh_instance
    mock_gh_repo = MagicMock()
    mock_gh_instance.get_repo.return_value = mock_gh_repo

    mock_ms = MagicMock()
    mock_ms.number = 1
    mock_ms.title = 'v1.0'
    mock_ms.description = 'First release'
    mock_ms.open_issues = 2
    mock_ms.closed_issues = 8
    mock_ms.due_on = datetime.datetime(2025, 12, 31)
    mock_ms.html_url = 'https://github.com/owner/repo1/milestone/1'

    mock_gh_repo.get_milestones.return_value = [mock_ms]

    response = client.get('/api/workspace/portfolio/milestones')
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 1
    assert data[0]['repo_name'] == 'repo1'
    assert data[0]['full_name'] == 'owner/repo1'
    assert data[0]['title'] == 'v1.0'
    assert data[0]['progress'] == 80.0
    assert data[0]['due_on'] == '2025-12-31T00:00:00'

def test_workspace_portfolio_milestones_unauthorized(client):
    response = client.get('/api/workspace/portfolio/milestones')
    assert response.status_code == 401

@patch('os.path.exists')
def test_workspace_portfolio_milestones_no_workspace(mock_exists, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_exists.return_value = False
    response = client.get('/api/workspace/portfolio/milestones')
    assert response.status_code == 200
    assert response.get_json() == []
