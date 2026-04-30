import pytest
from unittest.mock import MagicMock, patch
from flask import session

@pytest.fixture
def client():
    from app import create_app
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['github_token'] = 'test-token'
        yield client

def test_list_tasks_unauthorized():
    from app import create_app
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        response = client.get('/api/tasks')
        assert response.status_code == 401

@patch('app.tasks.routes.Github')
def test_list_tasks_success(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_user = MagicMock()
    mock_user.login = "testuser"
    mock_g.get_user.return_value = mock_user

    # Mock search results
    mock_issue = MagicMock()
    mock_issue.number = 1
    mock_issue.title = "Test Issue"
    mock_issue.repository.full_name = "owner/repo"
    mock_issue.pull_request = None
    mock_issue.updated_at = MagicMock()
    mock_issue.updated_at.isoformat.return_value = "2025-05-30T10:00:00"
    mock_issue.html_url = "http://github.com/owner/repo/issues/1"

    mock_pr = MagicMock()
    mock_pr.number = 2
    mock_pr.title = "Test PR"
    mock_pr.repository.full_name = "owner/repo"
    mock_pr.pull_request = MagicMock()
    mock_pr.updated_at = MagicMock()
    mock_pr.updated_at.isoformat.return_value = "2025-05-30T11:00:00"
    mock_pr.html_url = "http://github.com/owner/repo/pull/2"

    mock_pr_obj = MagicMock()
    mock_pr_obj.head.sha = "sha123"
    mock_pr.as_pull_request.return_value = mock_pr_obj

    mock_combined = MagicMock()
    mock_combined.state = "success"
    mock_pr.repository.get_combined_status.return_value = mock_combined

    # Setup search_issues to return these mocks for different queries
    # Category review_requested
    # Category assigned
    # Category authored
    mock_g.search_issues.side_effect = [
        [mock_pr], # review-requested
        [mock_issue], # assigned
        [] # author
    ]

    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 2
    # Sorted by updated_at desc, so PR (11:00) comes first
    assert data[0]['number'] == 2
    assert data[0]['category'] == 'review_requested'
    assert data[0]['ci_status'] == 'success'

    assert data[1]['number'] == 1
    assert data[1]['category'] == 'assigned'
    assert data[1]['type'] == 'issue'

@patch('app.tasks.routes.Github')
def test_list_tasks_error(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_g.get_user.side_effect = Exception("GitHub API Error")

    response = client.get('/api/tasks')
    assert response.status_code == 500
    assert "GitHub API Error" in response.get_json()['error']
