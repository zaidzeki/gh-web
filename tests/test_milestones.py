import pytest
from unittest.mock import MagicMock, patch
from flask import session
import datetime
import github

@pytest.fixture
def client():
    from app import create_app
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['github_token'] = 'test-token'
        yield client

@patch('app.milestones.routes.Github')
def test_list_milestones(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_ms = MagicMock()
    mock_ms.number = 1
    mock_ms.title = "v1.0"
    mock_ms.description = "First release"
    mock_ms.state = "open"
    mock_ms.open_issues = 5
    mock_ms.closed_issues = 10
    mock_ms.due_on = datetime.datetime(2025, 12, 31)
    mock_ms.html_url = "http://github.com/owner/repo/milestone/1"

    mock_repo.get_milestones.return_value = [mock_ms]

    response = client.get('/api/repos/owner/repo/milestones')
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 1
    assert data[0]['title'] == "v1.0"
    assert data[0]['open_issues'] == 5
    assert data[0]['closed_issues'] == 10

@patch('app.milestones.routes.Github')
def test_create_milestone(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_ms = MagicMock()
    mock_ms.number = 2
    mock_ms.title = "v2.0"
    mock_repo.create_milestone.return_value = mock_ms

    response = client.post('/api/repos/owner/repo/milestones', json={
        "title": "v2.0",
        "description": "Next release",
        "due_on": "2026-06-30T00:00:00Z"
    })

    assert response.status_code == 201
    assert response.get_json()['message'] == "Milestone created successfully"
    mock_repo.create_milestone.assert_called_once()

@patch('app.issues.routes.Github')
def test_update_issue_milestone(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_issue = MagicMock()
    mock_repo.get_issue.return_value = mock_issue

    mock_ms = MagicMock()
    mock_repo.get_milestone.return_value = mock_ms

    response = client.post('/api/repos/owner/repo/issues/1/milestone', json={
        "milestone_number": 1
    })

    assert response.status_code == 200
    mock_issue.edit.assert_called_with(milestone=mock_ms)

@patch('app.tasks.routes.github.Github')
@patch('app.tasks.routes.github.Auth')
def test_list_tasks_with_milestone_filter(mock_auth, mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_user = MagicMock()
    mock_user.login = "testuser"
    mock_g.get_user.return_value = mock_user

    mock_g.search_issues.return_value = []

    response = client.get('/api/tasks?milestone=v1.0')
    assert response.status_code == 200

    # Verify that milestone is included in search queries
    for call in mock_g.search_issues.call_args_list:
        assert 'milestone:"v1.0"' in call[0][0]
