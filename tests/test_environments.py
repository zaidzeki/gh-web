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

def test_list_environments(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    with patch('app.environments.routes.Github') as mock_github:
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo

        mock_env = MagicMock()
        mock_env.id = 123
        mock_env.name = 'production'
        mock_env.html_url = 'http://github.com/env/123'
        mock_env.created_at = None
        mock_env.updated_at = None

        mock_repo.get_environments.return_value = [mock_env]

        response = client.get('/api/repos/owner/repo/environments')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['name'] == 'production'

def test_list_deployments(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    with patch('app.environments.routes.Github') as mock_github:
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo

        mock_dep = MagicMock()
        mock_dep.id = 456
        mock_dep.sha = 'abcdef'
        mock_dep.ref = 'main'
        mock_dep.task = 'deploy'
        mock_dep.environment = 'production'
        mock_dep.description = 'First deploy'
        mock_dep.creator.login = 'user'
        mock_dep.created_at = None
        mock_dep.updated_at = None

        mock_status = MagicMock()
        mock_status.state = 'success'

        # PyGithub's PaginatedList doesn't behave like a list with totalCount
        # We need to mock the object that get_statuses() returns
        mock_statuses = MagicMock()
        mock_statuses.totalCount = 1
        mock_statuses.__getitem__.return_value = mock_status
        mock_dep.get_statuses.return_value = mock_statuses

        mock_repo.get_deployments.return_value = [mock_dep]

        response = client.get('/api/repos/owner/repo/deployments')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['status'] == 'success'

def test_create_deployment(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    with patch('app.environments.routes.Github') as mock_github:
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo

        mock_dep = MagicMock()
        mock_dep.id = 789
        mock_repo.create_deployment.return_value = mock_dep

        response = client.post('/api/repos/owner/repo/deployments', json={
            'ref': 'main',
            'environment': 'production'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['id'] == 789
        mock_repo.create_deployment.assert_called_with(
            ref='main',
            environment='production',
            description='',
            task='deploy',
            auto_merge=False,
            required_contexts=None
        )
