import pytest
from app import create_app
from unittest.mock import MagicMock, patch

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_get_user_orgs(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.auth.routes.get_github_client') as mock_github:
        mock_org = MagicMock()
        mock_org.login = 'testorg'
        mock_org.avatar_url = 'http://avatar.url/org'

        mock_github.return_value.get_user.return_value.get_orgs.return_value = [mock_org]

        response = client.get('/api/user/orgs')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['login'] == 'testorg'
        assert data[0]['avatar_url'] == 'http://avatar.url/org'

def test_list_repos_with_org(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.repos.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_repo.full_name = 'testorg/repo'
        mock_repo.name = 'repo'
        mock_repo.description = 'desc'
        mock_repo.html_url = 'http://github.com/testorg/repo'
        mock_repo.stargazers_count = 10
        mock_repo.open_issues_count = 5
        mock_repo.pushed_at = None
        mock_repo.private = False

        # Mock organization repos
        mock_github.return_value.get_organization.return_value.get_repos.return_value = [mock_repo]

        # Mock search_issues for PR counts
        mock_github.return_value.search_issues.return_value = []

        response = client.get('/api/repos?org=testorg')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['full_name'] == 'testorg/repo'

        mock_github.return_value.get_organization.assert_called_with('testorg')
