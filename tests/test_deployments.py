import pytest
from unittest.mock import MagicMock, patch
from flask import session

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

@patch('app.deployments.routes.Github')
def test_list_environments(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_env = MagicMock()
    mock_env.id = 1
    mock_env.name = "production"
    mock_env.html_url = "http://github.com/env"
    mock_env.created_at = MagicMock()
    mock_env.created_at.isoformat.return_value = "2023-01-01T00:00:00"
    mock_env.updated_at = MagicMock()
    mock_env.updated_at.isoformat.return_value = "2023-01-01T00:00:00"

    mock_repo.get_environments.return_value = [mock_env]
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.get('/api/repos/owner/repo/environments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == "production"

@patch('app.deployments.routes.Github')
def test_list_deployments(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_dep = MagicMock()
    mock_dep.id = 100
    mock_dep.environment = "production"
    mock_dep.ref = "main"
    mock_dep.sha = "abcdef123456"
    mock_dep.task = "deploy"
    mock_dep.description = "Test deployment"
    mock_dep.created_at = MagicMock()
    mock_dep.created_at.isoformat.return_value = "2023-01-01T00:00:00"
    mock_dep.updated_at = MagicMock()
    mock_dep.updated_at.isoformat.return_value = "2023-01-01T00:00:00"

    mock_status = MagicMock()
    mock_status.state = "success"
    mock_status.description = "Deployed successfully"
    mock_status.created_at = MagicMock()
    mock_status.created_at.isoformat.return_value = "2023-01-01T00:01:00"

    mock_statuses = MagicMock()
    mock_statuses.totalCount = 1
    mock_statuses.__getitem__.return_value = mock_status
    mock_dep.get_statuses.return_value = mock_statuses

    mock_dep.creator.login = "testuser"
    mock_dep.creator.avatar_url = "http://avatar.url"

    mock_repo.get_deployments.return_value = [mock_dep]
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.get('/api/repos/owner/repo/deployments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['environment'] == "production"
    assert data[0]['latest_status']['state'] == "success"

@patch('app.deployments.routes.Github')
def test_create_deployment(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_dep = MagicMock()
    mock_dep.id = 200
    mock_repo.create_deployment.return_value = mock_dep
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.post('/api/repos/owner/repo/deployments', json={
        'ref': 'main',
        'environment': 'production'
    })
    assert response.status_code == 201
    assert response.get_json()['id'] == 200
    mock_repo.create_deployment.assert_called_once()
