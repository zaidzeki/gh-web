import pytest
from unittest.mock import MagicMock, patch
from app import create_app

@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test'})
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_list_user_orgs_unauthorized(client):
    response = client.get('/api/user/orgs')
    assert response.status_code == 401

@patch('app.auth.routes.Github')
def test_list_user_orgs_success(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_org = MagicMock()
    mock_org.login = 'test-org'
    mock_org.avatar_url = 'http://example.com/avatar.png'
    mock_org.description = 'A test organization'

    mock_g.get_user.return_value.get_orgs.return_value = [mock_org]

    response = client.get('/api/user/orgs')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['login'] == 'test-org'
    assert data[0]['avatar_url'] == 'http://example.com/avatar.png'

@patch('app.repos.routes.Github')
def test_list_repos_with_org_context(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_repo = MagicMock()
    mock_repo.full_name = 'test-org/test-repo'
    mock_repo.name = 'test-repo'
    mock_repo.description = 'Test description'
    mock_repo.html_url = 'http://github.com/test-org/test-repo'
    mock_repo.stargazers_count = 10
    mock_repo.pushed_at = None
    mock_repo.private = False

    mock_org = MagicMock()
    mock_org.get_repos.return_value = [mock_repo]
    mock_g.get_organization.return_value = mock_org

    # Mock search_issues for counts
    mock_g.search_issues.return_value = []

    response = client.get('/api/repos?org_name=test-org')
    assert response.status_code == 200
    mock_g.get_organization.assert_called_with('test-org')
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['full_name'] == 'test-org/test-repo'

@patch('app.repos.routes.Github')
def test_list_repos_search_in_org_context(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_g.search_repositories.return_value = []
    mock_g.search_issues.return_value = []

    response = client.get('/api/repos?search=query&org_name=test-org')
    assert response.status_code == 200
    mock_g.search_repositories.assert_called()
    call_args = mock_g.search_repositories.call_args[0][0]
    assert "org:test-org" in call_args
    assert "query" in call_args
