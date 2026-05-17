import pytest
from unittest.mock import MagicMock, patch
from flask import session
import datetime
from app import create_app

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['github_token'] = 'test-token'
        yield client

@patch('app.repos.routes.Github')
def test_get_repos_health_with_milestones(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_repo = MagicMock()
    mock_repo.full_name = "owner/repo"
    mock_repo.default_branch = "main"
    mock_g.get_repo.return_value = mock_repo

    # Mock CI status
    mock_combined = MagicMock()
    mock_combined.state = "success"
    mock_combined.__str__.return_value = "success"
    mock_repo.get_combined_status.return_value = mock_combined

    # Mock Milestones
    mock_ms = MagicMock()
    mock_ms.title = "v1.0"
    mock_ms.due_on = datetime.datetime.now() + datetime.timedelta(days=7)
    mock_repo.get_milestones.return_value = [mock_ms]

    # Mock Environments
    mock_repo.get_environments.return_value = []

    response = client.get('/api/repos/health?repos=owner/repo')
    assert response.status_code == 200
    data = response.get_json()

    assert "owner/repo" in data
    health = data["owner/repo"]
    assert health["ci_status"] == "success"
    assert health["next_milestone"]["title"] == "v1.0"
    assert health["next_milestone"]["overdue"] is False

@patch('app.repos.routes.Github')
def test_get_repos_health_overdue_milestone(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_repo = MagicMock()
    mock_repo.full_name = "owner/repo"
    mock_repo.default_branch = "main"
    mock_g.get_repo.return_value = mock_repo

    # Mock Milestones
    mock_ms = MagicMock()
    mock_ms.title = "v0.9"
    mock_ms.due_on = datetime.datetime.now() - datetime.timedelta(days=7)
    mock_repo.get_milestones.return_value = [mock_ms]

    response = client.get('/api/repos/health?repos=owner/repo')
    assert response.status_code == 200
    data = response.get_json()

    health = data["owner/repo"]
    assert health["next_milestone"]["title"] == "v0.9"
    assert health["next_milestone"]["overdue"] is True

@patch('app.repos.routes.Github')
def test_get_repos_health_serialization(mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_repo = MagicMock()
    mock_repo.full_name = "owner/repo"
    mock_repo.default_branch = "main"
    mock_g.get_repo.return_value = mock_repo

    # Explicitly set return values to strings/ints to avoid MagicMock serialization errors
    mock_combined = MagicMock()
    mock_combined.state = "success"
    mock_repo.get_combined_status.return_value = mock_combined

    mock_ms = MagicMock()
    mock_ms.title = "v1.0"
    mock_ms.due_on = datetime.datetime.now()
    mock_repo.get_milestones.return_value = [mock_ms]

    response = client.get('/api/repos/health?repos=owner/repo')
    assert response.status_code == 200
