
import pytest
from app import create_app
from unittest.mock import MagicMock, patch

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_get_security_alerts_length_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    # Test full_name length
    long_name = 'a' * 256
    response = client.get(f'/api/repos/{long_name}/security/alerts')
    assert response.status_code == 400
    assert "Repository name is too long" in response.get_json()['error']

@patch('app.repos.routes.get_github_client')
def test_fetch_security_info_limits(mock_get_github_client, client):
    # Mocking github client and repo
    mock_g = MagicMock()
    mock_get_github_client.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    # Mock alerts with more than 100 items
    def create_mock_alert(i):
        alert = MagicMock()
        alert.number = i
        alert.security_advisory.severity = "high"
        alert.security_vulnerability.package.name = f"pkg-{i}"
        alert.security_vulnerability.first_patched_version_identifier = "1.0.1"
        alert.html_url = f"http://github.com/alert/{i}"
        alert.created_at = MagicMock()
        alert.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        return alert

    mock_dep_alerts = [create_mock_alert(i) for i in range(150)]
    mock_repo.get_dependabot_alerts.return_value = mock_dep_alerts

    mock_secret_alert = MagicMock()
    mock_secret_alert.secret_type = "token"
    mock_secret_alert.html_url = "http://github.com/secret"
    mock_secret_alerts = [mock_secret_alert] * 150
    mock_repo.get_secret_scanning_alerts.return_value = mock_secret_alerts

    mock_code_alert = MagicMock()
    mock_code_alert.rule.severity = "error"
    mock_code_alert.rule.description = "desc"
    mock_code_alert.html_url = "http://github.com/code"
    mock_code_alerts = [mock_code_alert] * 150
    mock_repo.get_codescan_alerts.return_value = mock_code_alerts

    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    response = client.get('/api/repos/owner/repo/security/alerts')
    assert response.status_code == 200
    data = response.get_json()

    # Verify that 'alerts' list is limited (up to 100 per category, so 300 total if all categories have 100+)
    # Dependabot alerts should be 100
    dep_alerts = [a for a in data['alerts'] if a['type'] == 'dependabot']
    assert len(dep_alerts) == 100

    # Secret alerts should be 100
    sec_alerts = [a for a in data['alerts'] if a['type'] == 'secret']
    assert len(sec_alerts) == 100

    # Code scanning alerts should be 100
    code_alerts = [a for a in data['alerts'] if a['type'] == 'code_scanning']
    assert len(code_alerts) == 100

    # Verify summary counts - for Secret and Code Scanning they are also updated inside the loop
    # Dependabot summary is also updated inside the loop
    assert data['summary']['vulnerabilities']['high'] == 100
    assert data['summary']['secrets']['open'] == 100
    assert data['summary']['code_scanning']['errors'] == 100
