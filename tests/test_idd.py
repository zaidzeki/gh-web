import pytest
from unittest.mock import MagicMock, patch
from app import create_app
import os
import shutil

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

@patch('app.workspace.routes.get_github_client')
@patch('git.Repo.clone_from')
@patch('git.Repo')
def test_setup_issue_fix(mock_repo_class, mock_clone, mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session_idd'

    # Mock Github repo for default branch
    mock_gh_repo = MagicMock()
    mock_gh_repo.default_branch = 'main'
    mock_github.return_value.get_repo.return_value = mock_gh_repo

    # Mock git Repo instance
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_clone.return_value = mock_repo

    # Mock remote and fetch
    mock_origin = MagicMock()
    mock_origin.url = 'https://github.com/owner/repo.git'
    mock_repo.remote.return_value = mock_origin

    # Mock git.GitCommandError for non-existent branch
    import git
    mock_repo.git.checkout.side_effect = [git.GitCommandError('checkout', 'fail'), None]

    # Test case: Clone doesn't exist yet
    response = client.post('/api/workspace/setup-issue-fix', json={
        'repo_full_name': 'owner/repo',
        'issue_number': 42
    })

    assert response.status_code == 200
    data = response.get_json()
    assert "Created and checked out fix branch 'fix/issue-42'" in data['message']
    assert data['branch'] == 'fix/issue-42'

    with client.session_transaction() as sess:
        assert sess['active_repo'] == 'repo'

    # Verify git calls
    mock_clone.assert_called_once()
    mock_origin.fetch.assert_called_once()
    mock_repo.git.checkout.assert_called_with('-B', 'fix/issue-42', 'origin/main')

@patch('app.workspace.routes.get_github_client')
@patch('git.Repo')
@patch('os.path.exists')
def test_setup_issue_fix_existing_branch(mock_exists, mock_repo_class, mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session_idd_existing'

    # Mock Github repo
    mock_gh_repo = MagicMock()
    mock_gh_repo.default_branch = 'main'
    mock_github.return_value.get_repo.return_value = mock_gh_repo

    # Mock exists for .git
    mock_exists.side_effect = lambda p: True if '.git' in p else False

    # Mock git Repo instance
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    # Mock remote
    mock_origin = MagicMock()
    mock_origin.url = 'https://github.com/owner/repo.git'
    mock_repo.remote.return_value = mock_origin

    # Mock checkout: first call (existing branch) succeeds
    mock_repo.git.checkout.return_value = "Switched to branch 'fix/issue-42'"

    response = client.post('/api/workspace/setup-issue-fix', json={
        'repo_full_name': 'owner/repo',
        'issue_number': 42
    })

    assert response.status_code == 200
    data = response.get_json()
    assert "Switched to existing fix branch 'fix/issue-42'" in data['message']
    mock_repo.git.checkout.assert_called_with('fix/issue-42')
