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

@patch('app.repos.routes.Github')
def test_create_repo_success(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_user = MagicMock()
    mock_repo = MagicMock()
    mock_repo.full_name = "testuser/testrepo"
    mock_repo.clone_url = "https://github.com/testuser/testrepo.git"
    mock_user.create_repo.return_value = mock_repo
    mock_github.return_value.get_user.return_value = mock_user

    response = client.post('/api/repos', json={
        'name': 'testrepo',
        'description': 'test desc',
        'visibility': 'public'
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == "Repository testrepo created successfully"
    assert data['full_name'] == "testuser/testrepo"
    mock_user.create_repo.assert_called_once_with('testrepo', description='test desc', private=False)

def test_create_repo_unauthorized(client):
    response = client.post('/api/repos', json={'name': 'testrepo'})
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}

def test_create_repo_no_name(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
    response = client.post('/api/repos', json={})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Repository name is required"}

@patch('app.repos.routes.get_github_client')
def test_list_orgs(mock_get_client, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_org = MagicMock()
    mock_org.login = "testorg"
    mock_org.avatar_url = "http://avatar.url"

    mock_github = MagicMock()
    mock_github.get_user.return_value.get_orgs.return_value = [mock_org]
    mock_get_client.return_value = mock_github

    response = client.get('/api/user/orgs')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['login'] == "testorg"
    assert data[0]['avatar_url'] == "http://avatar.url"

@patch('app.repos.routes.get_github_client')
def test_list_repos_org(mock_get_client, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_repo.full_name = "testorg/testrepo"
    mock_repo.name = "testrepo"
    mock_repo.description = "desc"
    mock_repo.html_url = "http://github.com/testorg/testrepo"
    mock_repo.stargazers_count = 5
    mock_repo.pushed_at = None
    mock_repo.private = False

    mock_github = MagicMock()
    mock_github.get_user.return_value.login = "testuser"
    mock_github.get_organization.return_value.get_repos.return_value = [mock_repo]

    # Mock search_issues for PR and Issue counts
    mock_pr = MagicMock()
    mock_pr.repository.full_name = "testorg/testrepo"
    mock_github.search_issues.return_value = [mock_pr]

    mock_get_client.return_value = mock_github

    response = client.get('/api/repos?org_name=testorg')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['full_name'] == "testorg/testrepo"
    mock_github.get_organization.assert_called_once_with("testorg")
