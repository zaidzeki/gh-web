import pytest
from unittest.mock import MagicMock, patch
from flask import session
import datetime

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

@patch('app.tasks.routes.github.Github')
@patch('app.tasks.routes.github.Auth')
def test_list_tasks_success(mock_auth, mock_github, client):
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
    mock_issue.updated_at = datetime.datetime(2025, 5, 30, 10, 0, 0)
    mock_issue.html_url = "http://github.com/owner/repo/issues/1"

    mock_pr = MagicMock()
    mock_pr.number = 2
    mock_pr.title = "Test PR"
    mock_pr.repository.full_name = "owner/repo"
    mock_pr.pull_request = MagicMock()
    mock_pr.updated_at = datetime.datetime(2025, 5, 30, 11, 0, 0)
    mock_pr.html_url = "http://github.com/owner/repo/pull/2"

    mock_pr_obj = MagicMock()
    mock_pr_obj.head.sha = "sha123"
    mock_pr_obj.get_reviews.return_value = []
    mock_pr.as_pull_request.return_value = mock_pr_obj

    mock_combined = MagicMock()
    mock_combined.state = "success"
    mock_pr.repository.get_combined_status.return_value = mock_combined

    # Setup search_issues to return these mocks for different queries
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

@patch('app.tasks.routes.github.Github')
@patch('app.tasks.routes.github.Auth')
def test_list_tasks_prioritization_and_deduplication(mock_auth, mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_user = MagicMock()
    mock_user.login = "testuser"
    mock_g.get_user.return_value = mock_user

    # PR that appears in all searches
    mock_pr = MagicMock()
    mock_pr.number = 10
    mock_pr.title = "Actionable PR"
    mock_pr.repository.full_name = "owner/repo"
    mock_pr.pull_request = MagicMock()
    mock_pr.updated_at = datetime.datetime(2025, 5, 30, 12, 0, 0)
    mock_pr.html_url = "http://github.com/owner/repo/pull/10"

    mock_pr_obj = MagicMock()
    mock_pr_obj.head.sha = "sha10"
    mock_pr_obj.get_reviews.return_value = []
    mock_pr.as_pull_request.return_value = mock_pr_obj
    mock_pr.repository.get_combined_status.side_effect = Exception("Status not found")

    # Setup search_issues to return same PR in all categories
    mock_g.search_issues.side_effect = [
        [mock_pr], # review-requested
        [mock_pr], # assigned
        [mock_pr]  # author
    ]

    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 1
    assert data[0]['number'] == 10
    assert data[0]['category'] == 'review_requested' # Highest priority category

@patch('app.tasks.routes.github.Github')
@patch('app.tasks.routes.github.Auth')
def test_list_tasks_review_status_enrichment(mock_auth, mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_user = MagicMock()
    mock_user.login = "testuser"
    mock_g.get_user.return_value = mock_user

    mock_pr = MagicMock()
    mock_pr.number = 20
    mock_pr.title = "Review Status PR"
    mock_pr.repository.full_name = "owner/repo"
    mock_pr.pull_request = MagicMock()
    mock_pr.updated_at = datetime.datetime(2025, 5, 30, 13, 0, 0)
    mock_pr.html_url = "http://github.com/owner/repo/pull/20"

    mock_pr_obj = MagicMock()
    mock_pr_obj.head.sha = "sha20"

    review1 = MagicMock()
    review1.state = "APPROVED"
    review2 = MagicMock()
    review2.state = "CHANGES_REQUESTED"
    mock_pr_obj.get_reviews.return_value = [review1, review2]

    mock_pr.as_pull_request.return_value = mock_pr_obj
    mock_pr.repository.get_combined_status.side_effect = Exception("Status not found")

    mock_g.search_issues.side_effect = [
        [], # review-requested
        [mock_pr], # assigned (PR in In Progress category)
        [] # author
    ]

    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 1
    assert data[0]['number'] == 20
    assert data[0]['category'] == 'assigned'
    assert data[0]['type'] == 'pr'
    assert data[0]['review_status'] == 'changes_requested' # CHANGES_REQUESTED prioritized over APPROVED

@patch('app.tasks.routes.github.Github')
def test_list_tasks_error(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_g.get_user.side_effect = Exception("GitHub API Error")

    response = client.get('/api/tasks')
    assert response.status_code == 500
    assert "GitHub API Error" in response.get_json()['error']
