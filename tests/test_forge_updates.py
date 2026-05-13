import pytest
from unittest.mock import MagicMock, patch
from app import create_app

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_logout(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['user_orgs'] = [{'login': 'test'}]

    response = client.post('/logout')
    assert response.status_code == 200
    assert response.get_json()['message'] == "Logged out successfully"

    with client.session_transaction() as sess:
        assert 'github_token' not in sess
        assert 'user_orgs' not in sess

def test_list_environments_enriched(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.deployments.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    # Mock environment
    mock_env = MagicMock()
    mock_env.name = 'production'
    mock_env.html_url = 'http://github.com/env/prod'
    mock_env.created_at = None
    mock_env.updated_at = None
    mock_repo.get_environments.return_value = [mock_env]

    # Mock deployment
    mock_deployment = MagicMock()
    mock_deployment.id = 1
    mock_deployment.sha = 'abc1234'
    mock_deployment.ref = 'v1.0.0'
    mock_deployment.environment = 'production'
    mock_deployment.created_at = None
    mock_deployment.creator.login = 'deployer'

    mock_status = MagicMock()
    mock_status.state = 'success'
    mock_status.description = 'Deployed successfully'
    mock_status.updated_at = None
    mock_deployment.get_statuses.return_value = [mock_status]

    mock_repo.get_deployments.return_value = [mock_deployment]

    response = client.get('/api/repos/owner/repo/environments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'production'
    assert data[0]['latest_deployment']['ref'] == 'v1.0.0'
    assert data[0]['latest_deployment']['latest_status']['state'] == 'success'

def test_production_health_synonyms(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.repos.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    # Mock environment with synonym 'live'
    mock_env = MagicMock()
    mock_env.name = 'live'
    mock_repo.get_environments.return_value = [mock_env]

    # Mock deployment for 'live'
    mock_deployment = MagicMock()
    mock_deployment.ref = 'v2.0.0'
    mock_repo.get_deployments.return_value = [mock_deployment]

    mock_status = MagicMock()
    mock_status.state = 'success'
    mock_deployment.get_statuses.return_value = [mock_status]

    # Mock CI Status
    mock_repo.default_branch = 'main'
    mock_combined = MagicMock()
    mock_combined.state = 'success'
    mock_repo.get_combined_status.return_value = mock_combined

    response = client.get('/api/repos/health?repos=owner/repo')
    assert response.status_code == 200
    data = response.get_json()
    assert 'owner/repo' in data
    assert data['owner/repo']['production_status']['env'] == 'live'
    assert data['owner/repo']['production_status']['ref'] == 'v2.0.0'
