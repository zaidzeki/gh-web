import pytest
from unittest.mock import MagicMock, patch
from app import create_app

@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_security_headers(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "upgrade-insecure-requests;" in response.headers["Content-Security-Policy"]
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert response.headers["Referrer-Policy"] == "no-referrer-when-downgrade"

@patch("app.repos.routes.get_github_client")
def test_list_teams_org_name_validation(mock_get_github, client):
    # Test long org name
    long_org = "a" * 101
    response = client.get(f"/api/user/orgs/{long_org}/teams")
    assert response.status_code == 400
    assert response.get_json()["error"] == "org_name is too long"

@patch("app.prs.routes.get_github_client")
def test_list_prs_limit(mock_get_github, client):
    with client.session_transaction() as sess:
        sess["github_token"] = "test-token"

    mock_g = MagicMock()
    mock_get_github.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    # Create 150 mock PRs
    mock_prs = []
    for i in range(150):
        pr = MagicMock()
        pr.number = i
        pr.title = f"PR {i}"
        pr.state = "open"
        pr.html_url = f"http://example.com/{i}"
        pr.user.login = "user"
        pr.head.repo = MagicMock()
        pr.head.repo.full_name = "org/repo"
        pr.head.repo.permissions.push = True
        pr.head.ref = "branch"
        pr.labels = []
        mock_prs.append(pr)

    mock_repo.get_pulls.return_value = mock_prs

    response = client.get("/api/repos/org/repo/prs")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 100
    assert data[0]["number"] == 0
    assert data[99]["number"] == 99

@patch("app.issues.routes.get_github_client")
def test_list_issues_limit(mock_get_github, client):
    with client.session_transaction() as sess:
        sess["github_token"] = "test-token"

    mock_g = MagicMock()
    mock_get_github.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    # Create 150 mock issues
    mock_issues = []
    for i in range(150):
        issue = MagicMock()
        issue.number = i
        issue.title = f"Issue {i}"
        issue.state = "open"
        issue.html_url = f"http://example.com/{i}"
        issue.user.login = "user"
        issue.created_at = None
        issue.labels = []
        issue.pull_request = None # Important: filter out PRs
        mock_issues.append(issue)

    mock_repo.get_issues.return_value = mock_issues

    response = client.get("/api/repos/org/repo/issues")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 100
    assert data[0]["number"] == 0
    assert data[99]["number"] == 99
