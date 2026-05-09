import pytest
from unittest.mock import MagicMock, patch
from flask import session

@pytest.fixture
def client():
    from app import create_app
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['github_token'] = 'test-token'
        yield client

@patch('app.deployments.routes.Github')
@patch('app.deployments.routes.Auth')
def test_list_environments_success(mock_auth, mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_env = MagicMock()
    mock_env.name = "production"
    mock_env.html_url = "http://github.com/owner/repo/environments/production"
    mock_env.created_at = None
    mock_env.updated_at = None
    mock_repo.get_environments.return_value = [mock_env]

    response = client.get('/api/repos/owner/repo/environments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == "production"

@patch('app.deployments.routes.Github')
@patch('app.deployments.routes.Auth')
def test_list_deployments_success(mock_auth, mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_deployment = MagicMock()
    mock_deployment.id = 123
    mock_deployment.environment = "production"
    mock_deployment.ref = "main"
    mock_deployment.sha = "sha123"
    mock_deployment.task = "deploy"
    mock_deployment.description = "Test"
    mock_deployment.created_at = None
    mock_deployment.updated_at = None
    mock_deployment.creator.login = "testuser"

    mock_status = MagicMock()
    mock_status.state = "success"
    mock_status.description = "Deployed"

    mock_statuses = MagicMock()
    mock_statuses.totalCount = 1
    mock_statuses.__getitem__.return_value = mock_status
    mock_deployment.get_statuses.return_value = mock_statuses

    mock_repo.get_deployments.return_value = [mock_deployment]

    response = client.get('/api/repos/owner/repo/deployments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 123
    assert data[0]['state'] == "success"

@patch('app.deployments.routes.Github')
@patch('app.deployments.routes.Auth')
def test_create_deployment_success(mock_auth, mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_deployment = MagicMock()
    mock_deployment.id = 456
    mock_repo.create_deployment.return_value = mock_deployment

    response = client.post('/api/repos/owner/repo/deployments', json={
        "ref": "main",
        "environment": "production"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] == 456
    mock_repo.create_deployment.assert_called_with(
        ref="main",
        environment="production",
        description="Deployed via GH-Web",
        auto_merge=False,
        required_contexts=[]
    )
