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

def test_list_tasks_includes_waiting_deployments(client, session_with_token):
    with patch('app.tasks.routes.github.Github') as mock_github:
        mock_user = MagicMock()
        mock_user.login = 'testuser'

        mock_repo = MagicMock()
        mock_repo.full_name = 'owner/repo'
        mock_repo.html_url = 'http://github.com/owner/repo'

        mock_dep = MagicMock()
        mock_dep.id = 999
        mock_dep.environment = 'production'

        mock_status = MagicMock()
        mock_status.state = 'waiting'
        mock_status.updated_at = None
        mock_dep.get_statuses.return_value = [mock_status]

        mock_repo.get_deployments.return_value = [mock_dep]
        mock_user.get_repos.return_value = [mock_repo]

        mock_github_instance = mock_github.return_value
        mock_github_instance.get_user.return_value = mock_user

        # Mock search_issues to return empty lists to focus on deployments
        mock_github_instance.search_issues.return_value = []

        response = client.get('/api/tasks')
        assert response.status_code == 200
        data = response.get_json()

        # Should have 1 task (the deployment)
        assert len(data) == 1
        assert data[0]['type'] == 'deployment'
        assert data[0]['number'] == 999
        assert 'waiting for approval' in data[0]['title']
