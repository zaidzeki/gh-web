import pytest
from unittest.mock import MagicMock, patch
from app import create_app
from datetime import datetime

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test'
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_github(app):
    with patch('app.deployments.routes.github.Github') as mock:
        yield mock

def test_list_environments(client, mock_github):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_env = MagicMock()
    mock_env.name = "production"
    mock_env.url = "http://prod.com"
    mock_env.html_url = "http://github.com/prod"
    mock_env.created_at = datetime(2023, 1, 1)
    mock_env.updated_at = datetime(2023, 1, 2)
    mock_repo.get_environments.return_value = [mock_env]

    # Mocking the client and its auth property
    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_g.get_repo.return_value = mock_repo

    response = client.get('/api/repos/owner/repo/environments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == "production"

def test_list_deployments(client, mock_github):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_deployment = MagicMock()
    mock_deployment.id = 123
    mock_deployment.sha = "abcdef"
    mock_deployment.ref = "main"
    mock_deployment.environment = "production"
    mock_deployment.created_at = datetime(2023, 1, 1)
    mock_deployment.updated_at = datetime(2023, 1, 1)
    mock_deployment.creator.login = "user"
    mock_deployment.task = "deploy"
    mock_deployment.description = "description"

    mock_status = MagicMock()
    mock_status.state = "success"
    mock_status.description = "Deployed"
    mock_status.created_at = datetime(2023, 1, 1)
    mock_status.creator.login = "user"

    mock_statuses = MagicMock()
    mock_statuses.totalCount = 1
    mock_statuses.__getitem__.return_value = mock_status
    mock_deployment.get_statuses.return_value = mock_statuses

    mock_repo.get_deployments.return_value = [mock_deployment]

    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_g.get_repo.return_value = mock_repo

    response = client.get('/api/repos/owner/repo/deployments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 123
    assert data[0]['latest_status']['state'] == "success"

def test_create_deployment(client, mock_github):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_deployment = MagicMock()
    mock_deployment.id = 456
    mock_deployment.environment = "staging"
    mock_repo.create_deployment.return_value = mock_deployment

    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_g.get_repo.return_value = mock_repo

    response = client.post('/api/repos/owner/repo/deployments', json={
        'ref': 'main',
        'environment': 'staging'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] == 456
    mock_repo.create_deployment.assert_called_once()

def test_create_deployment_status(client, mock_github):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_deployment = MagicMock()
    mock_status = MagicMock()
    mock_status.state = "success"
    mock_deployment.create_status.return_value = mock_status
    mock_repo.get_deployment.return_value = mock_deployment

    mock_g = MagicMock()
    mock_github.return_value = mock_g
    mock_g.get_repo.return_value = mock_repo

    response = client.post('/api/repos/owner/repo/deployments/123/status', json={
        'state': 'success',
        'description': 'Verified'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['state'] == "success"
    mock_deployment.create_status.assert_called_with(state='success', description='Verified')
