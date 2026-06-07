import pytest
from app import create_app
from unittest.mock import MagicMock, patch

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_remediation_suggestions_unauthorized(client):
    response = client.get('/api/governance/remediate/suggestions')
    assert response.status_code == 401

@patch('app.governance.routes.get_github_client')
def test_get_remediation_suggestions_success(mock_get_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_github = MagicMock()
    mock_get_github.return_value = mock_github

    mock_repo = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    # Mock dependabot alerts
    mock_alert = MagicMock()
    mock_alert.security_advisory.severity = 'critical'
    mock_alert.number = 1
    mock_alert.security_vulnerability.package.name = 'requests'
    mock_alert.security_vulnerability.first_patched_version_identifier = '2.31.0'
    mock_alert.created_at = None
    mock_alert.html_url = 'http://github.com/alert/1'

    mock_repo.get_dependabot_alerts.return_value = [mock_alert]
    mock_repo.get_secret_scanning_alerts.return_value = []
    mock_repo.get_codescan_alerts.return_value = []

    response = client.get('/api/governance/remediate/suggestions?repos=owner/repo1,owner/repo2')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['package'] == 'requests'
    assert data[0]['fixed_version'] == '2.31.0'
    assert 'owner/repo1' in data[0]['repos']
    assert 'owner/repo2' in data[0]['repos']

def test_remediate_batch_unauthorized(client):
    response = client.post('/api/governance/remediate/batch', json={
        "package": "requests",
        "fixed_version": "2.31.0",
        "repos": ["owner/repo1"]
    })
    assert response.status_code == 401

@patch('app.governance.routes.get_github_client')
def test_remediate_batch_success(mock_get_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_github = MagicMock()
    mock_get_github.return_value = mock_github

    mock_repo = MagicMock()
    mock_repo.permissions.push = True
    mock_repo.default_branch = 'main'
    mock_github.get_repo.return_value = mock_repo

    # Mock GitHub API calls for file fetching and updating
    mock_contents = MagicMock()
    mock_contents.decoded_content = b'requests==2.28.0\nother-pkg==1.0.0\n'
    mock_contents.sha = 'old-sha'
    mock_repo.get_contents.return_value = mock_contents

    mock_branch = MagicMock()
    mock_branch.commit.sha = 'head-sha'
    mock_repo.get_branch.return_value = mock_branch

    mock_pr = MagicMock()
    mock_pr.html_url = 'https://github.com/owner/repo1/pull/1'
    mock_repo.create_pull.return_value = mock_pr

    response = client.post('/api/governance/remediate/batch', json={
        "package": "requests",
        "fixed_version": "2.31.0",
        "repos": ["owner/repo1"]
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Batch remediation complete'
    assert data['results'][0]['status'] == 'success'
    assert data['results'][0]['detail'] == 'https://github.com/owner/repo1/pull/1'

    # Verify update_file was called with patched content
    mock_repo.update_file.assert_called_once()
    args, kwargs = mock_repo.update_file.call_args
    assert 'requests==2.31.0\n' in kwargs['content']
