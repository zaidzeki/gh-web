import pytest
from unittest.mock import MagicMock, patch
from app import create_app
import os

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
def test_setup_issue_fix_linkage(mock_repo_class, mock_clone, mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session_idd_linkage'

    mock_gh_repo = MagicMock()
    mock_gh_repo.default_branch = 'main'
    mock_issue = MagicMock()
    mock_issue.title = 'Test Issue'
    mock_gh_repo.get_issue.return_value = mock_issue
    mock_github.return_value.get_repo.return_value = mock_gh_repo

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_clone.return_value = mock_repo

    mock_origin = MagicMock()
    mock_origin.url = 'https://github.com/owner/repo.git'
    mock_repo.remote.return_value = mock_origin

    import git
    mock_repo.git.checkout.side_effect = [git.GitCommandError('checkout', 'fail'), None]

    response = client.post('/api/workspace/setup-issue-fix', json={
        'repo_full_name': 'owner/repo',
        'issue_number': 123
    })

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess['active_issues']['repo']['number'] == 123
        assert sess['active_issues']['repo']['title'] == 'Test Issue'

@patch('git.Repo')
@patch('app.workspace.routes.os.path.exists')
@patch('app.workspace.routes.os.makedirs')
def test_workspace_status_with_issue(mock_makedirs, mock_exists, mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['active_issues'] = {'testrepo': 123}
        sess['session_id'] = 'test_session_status'

    mock_exists.side_effect = lambda p: True if '.git' in p else True
    mock_repo = MagicMock()
    mock_repo.active_branch.name = 'fix/issue-123'
    mock_repo.is_dirty.return_value = False
    mock_repo.untracked_files = []
    mock_repo_class.return_value = mock_repo

    response = client.get('/api/workspace/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['active_issue'] == 123

@patch('git.Repo')
@patch('app.workspace.routes.os.path.exists')
@patch('app.workspace.routes.os.makedirs')
def test_workspace_status_with_issue_object(mock_makedirs, mock_exists, mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['active_issues'] = {'testrepo': {'number': 123, 'title': 'Test Issue', 'default_branch': 'main'}}
        sess['session_id'] = 'test_session_status_obj'

    mock_exists.side_effect = lambda p: True if '.git' in p else True
    mock_repo = MagicMock()
    mock_repo.active_branch.name = 'fix/issue-123'
    mock_repo.is_dirty.return_value = False
    mock_repo.untracked_files = []
    mock_repo_class.return_value = mock_repo

    response = client.get('/api/workspace/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['active_issue'] == 123
    assert data['issue_title'] == 'Test Issue'
    assert data['default_branch'] == 'main'
