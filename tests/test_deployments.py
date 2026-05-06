import pytest
from unittest.mock import MagicMock
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

def test_list_environments(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.deployments.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_env = MagicMock()
    mock_env.name = 'production'
    mock_repo.get_environments.return_value = [mock_env]

    response = client.get('/api/repos/owner/repo/environments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'production'

def test_list_deployments(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.deployments.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_deployment = MagicMock()
    mock_deployment.id = 123
    mock_deployment.environment = 'production'
    mock_deployment.ref = 'main'
    mock_deployment.sha = 'abcdef123456'
    mock_deployment.description = 'Test deployment'
    mock_deployment.created_at = None
    mock_deployment.updated_at = None
    mock_deployment.creator.login = 'testuser'

    mock_status = MagicMock()
    mock_status.state = 'success'
    mock_statuses = MagicMock()
    mock_statuses.totalCount = 1
    mock_statuses.__getitem__.return_value = mock_status
    mock_deployment.get_statuses.return_value = mock_statuses

    mock_repo.get_deployments.return_value = [mock_deployment]

    response = client.get('/api/repos/owner/repo/deployments?environment=production')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 123
    assert data[0]['state'] == 'success'

def test_create_deployment(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.deployments.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_deployment = MagicMock()
    mock_deployment.id = 456
    mock_repo.create_deployment.return_value = mock_deployment

    response = client.post('/api/repos/owner/repo/deployments', json={
        'ref': 'main',
        'environment': 'production',
        'description': 'Deploying main'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] == 456
    assert 'Deployment created successfully' in data['message']
