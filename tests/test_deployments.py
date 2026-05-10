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

def test_list_environments_unauthorized(client):
    response = client.get('/api/repos/owner/repo/environments')
    assert response.status_code == 401

@patch('app.deployments.routes.get_github_client')
def test_list_environments_success(mock_get_github, client):
    mock_g = MagicMock()
    mock_get_github.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_env = MagicMock()
    mock_env.name = "production"
    mock_env.html_url = "http://github.com/owner/repo/deployments/production"
    mock_repo.get_environments.return_value = [mock_env]

    mock_deployment = MagicMock()
    mock_deployment.id = 123
    mock_deployment.ref = "main"
    mock_deployment.sha = "abc1234"
    mock_deployment.task = "deploy"
    mock_deployment.environment = "production"
    mock_deployment.created_at = None
    mock_repo.get_deployments.return_value = [mock_deployment]

    mock_status = MagicMock()
    mock_status.state = "success"
    mock_status.description = "Deployed successfully"
    mock_status.updated_at = None
    mock_deployment.get_statuses.return_value = [mock_status]

    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    response = client.get('/api/repos/owner/repo/environments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == "production"
    assert data[0]['latest_deployment']['status']['state'] == "success"

@patch('app.deployments.routes.get_github_client')
def test_create_deployment_success(mock_get_github, client):
    mock_g = MagicMock()
    mock_get_github.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_deployment = MagicMock()
    mock_deployment.id = 999
    mock_repo.create_deployment.return_value = mock_deployment

    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    response = client.post('/api/repos/owner/repo/deployments', data={
        'ref': 'main',
        'environment': 'production'
    })

    assert response.status_code == 201
    assert response.get_json()['id'] == 999
    mock_repo.create_deployment.assert_called_once_with(
        ref='main',
        environment='production',
        description='Deployed via GH-Web',
        task='deploy',
        auto_merge=False
    )
