import pytest
import os
import shutil
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

@pytest.fixture
def mock_git_repo():
    with patch('git.Repo') as mock:
        repo = mock.return_value
        repo.active_branch.name = 'main'

        mock_tracking = MagicMock()
        mock_tracking.name = 'origin/main'
        mock_tracking.remote_name = 'origin'
        repo.active_branch.tracking_branch.return_value = mock_tracking

        repo.git.rev_list.return_value = "2 1" # ahead 2, behind 1
        repo.head.commit.summary = "Test commit"
        repo.head.commit.hexsha = "abc123sha"
        repo.is_dirty.return_value = False
        repo.untracked_files = []

        mock_remote = MagicMock()
        mock_remote.url = 'https://github.com/owner/repo.git'
        repo.remote.return_value = mock_remote
        repo.remotes = [mock_remote]

        yield mock

def test_portfolio_enriched_data(client, mock_git_repo):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['session_id'] = 'test-session'
        sess['active_issues'] = {
            'test-repo': {
                'number': 123,
                'title': 'Test Issue',
                'is_pr': False
            }
        }

    workspace_root = '/tmp/gh-web-workspaces/test-session'
    repo_path = os.path.join(workspace_root, 'test-repo')
    os.makedirs(os.path.join(repo_path, '.git'), exist_ok=True)

    try:
        response = client.get('/api/workspace/portfolio')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        item = data[0]
        assert item['repo_name'] == 'test-repo'
        assert item['ahead'] == 2
        assert item['behind'] == 1
        assert item['last_commit_subject'] == 'Test commit'
        assert item['active_issue']['number'] == 123
        assert item['active_issue']['title'] == 'Test Issue'
    finally:
        if os.path.exists(workspace_root):
            shutil.rmtree(workspace_root)

def test_sync_all_workspaces(client, mock_git_repo):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['session_id'] = 'sync-session'

    workspace_root = '/tmp/gh-web-workspaces/sync-session'
    os.makedirs(os.path.join(workspace_root, 'repo1', '.git'), exist_ok=True)
    os.makedirs(os.path.join(workspace_root, 'repo2', '.git'), exist_ok=True)

    try:
        response = client.post('/api/workspace/sync-all')
        assert response.status_code == 200
        data = response.get_json()
        assert 'Successfully synced 2 repositories' in data['message']
        assert 'repo1' in data['synced']
        assert 'repo2' in data['synced']

        # Verify fetch was called on the mock remote
        assert mock_git_repo.return_value.remotes[0].fetch.called
    finally:
        if os.path.exists(workspace_root):
            shutil.rmtree(workspace_root)

@patch('app.workspace.routes.Github')
def test_workspace_status_ci(mock_github_class, client, mock_git_repo):
    mock_gh = mock_github_class.return_value
    mock_gh_repo = MagicMock()
    mock_gh.get_repo.return_value = mock_gh_repo

    # Mock permissions as requested by memory
    mock_gh_repo.permissions.push = True

    mock_status = MagicMock()
    mock_status.state = 'success'
    mock_gh_repo.get_combined_status.return_value = mock_status

    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['session_id'] = 'ci-session'
        sess['active_repo'] = 'ci-repo'
        sess['active_issues'] = {
            'ci-repo': {
                'repo_full_name': 'owner/ci-repo'
            }
        }

    workspace_root = '/tmp/gh-web-workspaces/ci-session'
    repo_path = os.path.join(workspace_root, 'ci-repo')
    os.makedirs(os.path.join(repo_path, '.git'), exist_ok=True)

    try:
        response = client.get('/api/workspace/status')
        if response.status_code != 200:
            print(response.get_json())
        assert response.status_code == 200
        data = response.get_json()
        assert data['ci_status'] == 'success'
    finally:
        if os.path.exists(workspace_root):
            shutil.rmtree(workspace_root)
