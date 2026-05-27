import pytest
from flask import session
from app import create_app
from unittest.mock import MagicMock, patch

@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test'})
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@patch('app.repos.routes.Github')
def test_get_security_alerts(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_github.return_value.get_repo.return_value = mock_repo

    # Mock Dependabot Alerts
    mock_dep_alert = MagicMock()
    mock_dep_alert.security_advisory.severity = 'critical'
    mock_dep_alert.security_vulnerability.package.name = 'django'
    mock_dep_alert.security_vulnerability.first_patched_version_identifier = '4.2.1'
    mock_dep_alert.html_url = 'http://example.com/dep/1'
    mock_repo.get_dependabot_alerts.return_value = [mock_dep_alert]

    # Mock Secret Scanning Alerts
    mock_secret_alert = MagicMock()
    mock_secret_alert.state = 'open'
    mock_repo.get_secret_scanning_alerts.return_value = [mock_secret_alert]

    # Mock Code Scanning Alerts
    mock_code_alert = MagicMock()
    mock_code_alert.rule.severity = 'error'
    mock_repo.get_codescan_alerts.return_value = [mock_code_alert]

    response = client.get('/api/repos/owner/repo/security/alerts')
    assert response.status_code == 200
    data = response.get_json()

    assert 'summary' in data
    assert data['summary']['vulnerabilities']['critical'] == 1
    assert data['summary']['secrets']['open'] == 1
    assert data['summary']['code_scanning']['errors'] == 1
    assert len(data['alerts']) > 0

@patch('app.repos.routes.Github')
def test_repo_health_with_security(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_github.return_value.get_repo.return_value = mock_repo

    # Mock other health info to avoid failures
    mock_repo.get_combined_status.return_value.state = 'success'
    mock_repo.get_milestones.return_value = []
    mock_repo.get_environments.return_value = []

    # Mock Security Alerts for health check
    mock_dep_alert = MagicMock()
    mock_dep_alert.security_advisory.severity = 'critical'
    mock_repo.get_dependabot_alerts.return_value = [mock_dep_alert]
    mock_repo.get_secret_scanning_alerts.return_value = []
    mock_repo.get_codescan_alerts.return_value = []

    response = client.get('/api/repos/health?repos=owner/repo')
    assert response.status_code == 200
    data = response.get_json()

    assert 'owner/repo' in data
    assert data['owner/repo']['security_status'] == 'failure'
    assert data['owner/repo']['security_summary']['vulnerabilities']['critical'] == 1
