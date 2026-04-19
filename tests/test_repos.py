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
