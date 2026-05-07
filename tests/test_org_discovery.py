import pytest
from app import create_app
from unittest.mock import MagicMock, patch
import json

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_list_user_orgs(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.auth.routes.get_github_client') as mock_github:
        mock_org = MagicMock()
        mock_org.login = 'testorg'
        mock_org.avatar_url = 'http://avatar.url/org'
        mock_org.description = 'Test Org Description'

        mock_github.return_value.get_user.return_value.get_orgs.return_value = [mock_org]

        response = client.get('/api/user/orgs')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['login'] == 'testorg'
        assert data[0]['description'] == 'Test Org Description'

def test_list_org_repos(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.repos.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_repo.full_name = 'testorg/repo'
        mock_repo.name = 'repo'
        mock_repo.description = 'desc'
        mock_repo.html_url = 'http://github.com/testorg/repo'
        mock_repo.stargazers_count = 0
        mock_repo.pushed_at = None
        mock_repo.private = False

        mock_org = MagicMock()
        mock_org.get_repos.return_value = [mock_repo]

        mock_github.return_value.get_organization.return_value = mock_org
        mock_github.return_value.get_user.return_value.login = 'testuser'

        # Mock search_issues for PR counts - ensure we use context-aware query
        mock_pr = MagicMock()
        mock_pr.repository.full_name = 'testorg/repo'

        # Capture the query passed to search_issues
        def search_issues_side_effect(query, **kwargs):
            if "org:testorg" in query:
                return [mock_pr]
            return []

        mock_github.return_value.search_issues.side_effect = search_issues_side_effect

        response = client.get('/api/repos?org_name=testorg')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['full_name'] == 'testorg/repo'
        assert data[0]['open_prs_count'] == 1

def test_search_org_repos(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.repos.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_repo.full_name = 'testorg/search-result'
        mock_repo.name = 'search-result'
        mock_repo.description = 'desc'
        mock_repo.html_url = 'http://github.com/testorg/search-result'
        mock_repo.stargazers_count = 0
        mock_repo.pushed_at = None
        mock_repo.private = False

        mock_github.return_value.search_repositories.return_value = [mock_repo]
        mock_github.return_value.get_user.return_value.login = 'testuser'

        response = client.get('/api/repos?org_name=testorg&search=query')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['full_name'] == 'testorg/search-result'

        # Verify search query
        mock_github.return_value.search_repositories.assert_called_with('org:testorg query')
