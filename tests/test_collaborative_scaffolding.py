import os
import shutil
import pytest
from unittest.mock import MagicMock, patch
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret",
        "SESSION_COOKIE_SECURE": False
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_github():
    with patch('app.workspace.routes.get_github_client') as mock:
        g = MagicMock()
        mock.return_value = g
        yield g

@pytest.fixture
def setup_template():
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    os.makedirs(templates_root, exist_ok=True)
    template_name = "test-template"
    template_path = os.path.join(templates_root, template_name)
    if os.path.exists(template_path):
        shutil.rmtree(template_path)
    os.makedirs(template_path)
    with open(os.path.join(template_path, "README.md"), "w") as f:
        f.write("# Test Template")

    yield template_name

    if os.path.exists(template_path):
        shutil.rmtree(template_path)

def test_publish_template_success(client, mock_github, setup_template):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test_token'

    # Mock user and repo creation
    mock_user = mock_github.get_user.return_value
    mock_repo = MagicMock()
    mock_repo.full_name = "testuser/test-template-repo"
    mock_repo.html_url = "https://github.com/testuser/test-template-repo"
    mock_repo.clone_url = "https://github.com/testuser/test-template-repo.git"
    mock_user.create_repo.return_value = mock_repo

    with patch('git.Repo.clone_from') as mock_clone:
        mock_local_repo = MagicMock()
        mock_clone.return_value = mock_local_repo

        response = client.post(f'/api/workspace/templates/{setup_template}/publish', json={
            'name': 'test-template-repo',
            'description': 'A test description',
            'visibility': 'public'
        })

    if response.status_code != 201:
        print(response.get_json())
    assert response.status_code == 201
    data = response.get_json()
    assert "published successfully" in data['message']
    assert data['full_name'] == "testuser/test-template-repo"

    mock_user.create_repo.assert_called_once_with(
        'test-template-repo',
        description='A test description',
        private=False
    )
    mock_clone.assert_called_once()
    mock_local_repo.git.add.assert_called_with(A=True)
    mock_local_repo.index.commit.assert_called()
    mock_local_repo.git.push.assert_called_with('origin', 'main')

def test_publish_template_unauthorized(client, setup_template):
    # No token in session
    response = client.post(f'/api/workspace/templates/{setup_template}/publish')
    assert response.status_code == 401

def test_publish_template_not_found(client, mock_github):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test_token'

    response = client.post('/api/workspace/templates/non-existent/publish')
    assert response.status_code == 404
