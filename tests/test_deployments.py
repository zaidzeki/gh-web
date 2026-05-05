import pytest
from unittest.mock import MagicMock, patch
from app import create_app

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def session_with_token(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'

def test_list_environments_success(client, session_with_token):
    with patch('app.deployments.routes.Github') as mock_github:
        mock_repo = MagicMock()
        mock_env = MagicMock()
        mock_env.name = 'production'
        mock_env.url = 'http://api.github.com/envs/prod'
        mock_env.html_url = 'http://github.com/owner/repo/deployments/production'
        mock_env.created_at = None
        mock_env.updated_at = None

        mock_repo.get_environments.return_value = [mock_env]
        mock_github.return_value.get_repo.return_value = mock_repo

        response = client.get('/api/repos/owner/repo/environments')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['name'] == 'production'

def test_list_deployments_success(client, session_with_token):
    with patch('app.deployments.routes.Github') as mock_github:
        mock_repo = MagicMock()
        mock_dep = MagicMock()
        mock_dep.id = 123
        mock_dep.sha = 'abc'
        mock_dep.ref = 'main'
        mock_dep.task = 'deploy'
        mock_dep.environment = 'production'
        mock_dep.description = 'test'
        mock_dep.created_at = None
        mock_dep.updated_at = None
        mock_dep.creator.login = 'user'

        mock_status = MagicMock()
        mock_status.state = 'success'
        mock_status.description = 'ok'
        mock_status.updated_at = None
        mock_dep.get_statuses.return_value = [mock_status]

        mock_repo.get_deployments.return_value = [mock_dep]
        mock_github.return_value.get_repo.return_value = mock_repo

        response = client.get('/api/repos/owner/repo/deployments')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['id'] == 123
        assert data[0]['latest_status']['state'] == 'success'

def test_create_deployment_success(client, session_with_token):
    with patch('app.deployments.routes.Github') as mock_github:
        mock_repo = MagicMock()
        mock_dep = MagicMock()
        mock_dep.id = 456
        mock_dep.sha = 'def'
        mock_repo.create_deployment.return_value = mock_dep
        mock_github.return_value.get_repo.return_value = mock_repo

        response = client.post('/api/repos/owner/repo/deployments', json={
            'ref': 'main',
            'environment': 'production'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['id'] == 456
        assert 'triggered successfully' in data['message']
