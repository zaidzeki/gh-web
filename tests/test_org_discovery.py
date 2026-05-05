import pytest
from app import create_app
from unittest.mock import MagicMock, patch
import json

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_get_user_orgs(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.auth.routes.get_github_client') as mock_github:
        mock_user = MagicMock()
        mock_org = MagicMock()
        mock_org.login = 'testorg'
        mock_org.avatar_url = 'http://org.url'
        mock_org.description = 'desc'

        mock_github.return_value.get_user.return_value.get_orgs.return_value = [mock_org]

        # First call - should fetch and cache
        response = client.get('/api/user/orgs')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['login'] == 'testorg'

        with client.session_transaction() as sess:
            assert 'user_orgs' in sess
            assert sess['user_orgs'][0]['login'] == 'testorg'

        # Second call - should use cache
        mock_github.return_value.get_user.return_value.get_orgs.reset_mock()
        response = client.get('/api/user/orgs')
        assert response.status_code == 200
        mock_github.return_value.get_user.return_value.get_orgs.assert_not_called()

def test_list_repos_with_org(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.repos.routes.get_github_client') as mock_github:
        mock_org = MagicMock()
        mock_repo = MagicMock()
        mock_repo.full_name = 'testorg/repo'
        mock_repo.name = 'repo'
        mock_repo.description = 'desc'
        mock_repo.html_url = 'http://github.com/testorg/repo'
        mock_repo.stargazers_count = 10
        mock_repo.open_issues_count = 5
        mock_repo.pushed_at = None
        mock_repo.private = False

        mock_github.return_value.get_organization.return_value = mock_org
        mock_org.get_repos.return_value = [mock_repo]

        # Mock search_issues for PR/Issue counts
        mock_pr = MagicMock()
        mock_pr.repository.full_name = 'testorg/repo'
        mock_github.return_value.search_issues.return_value = [mock_pr]

        response = client.get('/api/repos?org_name=testorg')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['full_name'] == 'testorg/repo'

        mock_github.return_value.get_organization.assert_called_with('testorg')

def test_list_tasks_with_org(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.tasks.routes.get_github_client') as mock_github:
        mock_user = MagicMock()
        mock_user.login = 'testuser'
        mock_github.return_value.get_user.return_value = mock_user

        mock_github.return_value.search_issues.return_value = []

        response = client.get('/api/tasks?org_name=testorg')
        assert response.status_code == 200

        # Verify search filters include the org
        calls = mock_github.return_value.search_issues.call_args_list
        for call in calls:
            query = call[0][0]
            assert 'org:testorg' in query
            assert 'user:testuser' not in query
