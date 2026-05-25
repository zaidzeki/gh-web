import pytest
from app import create_app
from unittest.mock import MagicMock, patch

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-key"
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@patch("app.repos.routes.Github")
def test_list_teams(mock_github, client):
    with client.session_transaction() as sess:
        sess["github_token"] = "test-token"

    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_team = MagicMock()
    mock_team.id = 123
    mock_team.name = "Test Team"
    mock_team.slug = "test-team"
    mock_team.organization.login = "test-org"

    mock_g.get_user().get_teams.return_value = [mock_team]

    response = client.get("/api/user/orgs/test-org/teams")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == 123
    assert data[0]["name"] == "Test Team"

@patch("app.repos.routes.Github")
def test_list_repos_with_team(mock_github, client):
    with client.session_transaction() as sess:
        sess["github_token"] = "test-token"

    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_org = MagicMock()
    mock_g.get_organization.return_value = mock_org

    mock_repo = MagicMock()
    mock_repo.full_name = "test-org/test-repo"
    mock_repo.name = "test-repo"
    mock_repo.description = "Test Desc"
    mock_repo.pushed_at = None

    mock_org.get_team.return_value.get_repos.return_value = [mock_repo]
    mock_g.get_user().get_repos.return_value = []

    # Mock search_issues for PR/Issue counts
    mock_g.search_issues.return_value = []

    response = client.get("/api/repos?org_name=test-org&team_id=123")
    if response.status_code != 200:
        print(response.get_json())
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["full_name"] == "test-org/test-repo"

@patch("app.tasks.routes.github.Github")
def test_list_tasks_with_team(mock_github, client):
    with client.session_transaction() as sess:
        sess["github_token"] = "test-token"

    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_g.get_user().login = "test-user"

    # Mock search_issues for the 4 categories
    mock_issue = MagicMock()
    mock_issue.repository.full_name = "org/repo"
    mock_issue.number = 1
    mock_issue.title = "Team Task"
    mock_issue.pull_request = None
    mock_issue.updated_at = None
    mock_issue.milestone = None

    # Mocking 4 calls to search_issues (Review Requests, In Progress, My PRs, Waiting Deployment)
    mock_g.search_issues.side_effect = [
        [mock_issue], # Action Required
        [], # In Progress
        [], # My PRs
        []  # Waiting Deployment
    ]

    response = client.get("/api/tasks?org_name=test-org&team_slug=test-team")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["title"] == "Team Task"

    # Verify that the search query included the team filter
    args, kwargs = mock_g.search_issues.call_args_list[0]
    assert "team-review-requested:test-org/test-team" in args[0]
