import pytest
from unittest.mock import MagicMock, patch
from app import create_app
import os
import shutil
import tempfile

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

def test_save_template(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    # Create dummy workspace content
    workspace_dir = '/tmp/gh-web-workspaces/test_session/testrepo'
    os.makedirs(workspace_dir, exist_ok=True)
    with open(os.path.join(workspace_dir, 'README.md'), 'w') as f:
        f.write("# Test Repo")
    os.makedirs(os.path.join(workspace_dir, '.git'), exist_ok=True)

    response = client.post('/api/workspace/save-template', json={'template_name': 'test-template'})
    assert response.status_code == 201
    assert "saved successfully" in response.get_json()['message']

    templates_root = os.path.expanduser('~/.zekiprod/templates')
    assert os.path.exists(os.path.join(templates_root, 'test-template/README.md'))
    assert not os.path.exists(os.path.join(templates_root, 'test-template/.git'))

def test_list_templates(client):
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    os.makedirs(os.path.join(templates_root, 't1'), exist_ok=True)
    os.makedirs(os.path.join(templates_root, 't2'), exist_ok=True)

    response = client.get('/api/workspace/templates')
    assert response.status_code == 200
    templates = response.get_json()
    assert 't1' in templates
    assert 't2' in templates

@patch('app.repos.routes.Github')
@patch('git.Repo.clone_from')
def test_create_repo_with_template(mock_clone, mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    # Prepare template
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    template_path = os.path.join(templates_root, 'test-template')
    os.makedirs(template_path, exist_ok=True)
    with open(os.path.join(template_path, 'boilerplate.txt'), 'w') as f:
        f.write("boilerplate content")

    # Mock Github
    mock_user = MagicMock()
    mock_repo = MagicMock()
    mock_repo.clone_url = "https://github.com/owner/newrepo.git"
    mock_repo.full_name = "owner/newrepo"
    mock_user.create_repo.return_value = mock_repo
    mock_github.return_value.get_user.return_value = mock_user

    # Mock Git Repo
    mock_local_repo = MagicMock()
    mock_clone.return_value = mock_local_repo

    response = client.post('/api/repos/create', json={
        'name': 'newrepo',
        'template_name': 'test-template'
    })

    assert response.status_code == 201
    assert "with template" in response.get_json()['message']

    mock_user.create_repo.assert_called_once_with('newrepo', description='', private=False)
    mock_clone.assert_called_once()
    mock_local_repo.git.add.assert_called()
    mock_local_repo.index.commit.assert_called_with("Initial commit from template")
    mock_local_repo.git.push.assert_called_with('origin', 'main')
