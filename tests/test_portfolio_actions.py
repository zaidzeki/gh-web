import pytest
import os
import shutil
from app import create_app
from unittest.mock import MagicMock, patch

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_sync_workspace_action(client):
    with client.session_transaction() as sess:
        sess['session_id'] = 'test-session'
        sess['active_repo'] = 'test-repo'

    workspace_root = '/tmp/gh-web-workspaces/test-session'
    repo_path = os.path.join(workspace_root, 'test-repo')
    os.makedirs(os.path.join(repo_path, '.git'), exist_ok=True)

    with patch('git.Repo') as mock_repo_class:
        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_repo.remotes = [mock_remote]
        mock_repo_class.return_value = mock_repo

        # Test Sync
        response = client.post('/api/workspace/sync')
        assert response.status_code == 200
        assert mock_remote.fetch.called

    shutil.rmtree(workspace_root)

def test_discard_workspace_action(client):
    with client.session_transaction() as sess:
        sess['session_id'] = 'test-session'
        sess['active_repo'] = 'test-repo'

    workspace_root = '/tmp/gh-web-workspaces/test-session'
    repo_path = os.path.join(workspace_root, 'test-repo')
    os.makedirs(os.path.join(repo_path, '.git'), exist_ok=True)

    with patch('git.Repo') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Simulate that commits exist
        mock_repo.head.commit = MagicMock()

        # Test Discard (Revert)
        response = client.post('/api/workspace/revert')
        assert response.status_code == 200
        mock_repo.git.reset.assert_called_with('--hard', 'HEAD')
        mock_repo.git.clean.assert_called_with('-fd')

    shutil.rmtree(workspace_root)

def test_discard_workspace_no_commits(client):
    with client.session_transaction() as sess:
        sess['session_id'] = 'test-session'
        sess['active_repo'] = 'test-repo'

    workspace_root = '/tmp/gh-web-workspaces/test-session'
    repo_path = os.path.join(workspace_root, 'test-repo')
    os.makedirs(os.path.join(repo_path, '.git'), exist_ok=True)

    # Create a dummy file to be deleted
    with open(os.path.join(repo_path, 'untracked.txt'), 'w') as f:
        f.write('hello')

    with patch('git.Repo') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Simulate no commits exist by raising AttributeError or ValueError when accessing head.commit
        # In routes.py: try: repo.head.commit except (ValueError, git.GitCommandError):
        from git import GitCommandError
        type(mock_repo.head).commit = property(MagicMock(side_effect=ValueError("No commits")))

        # Test Discard (Revert) for empty repo
        response = client.post('/api/workspace/revert')
        assert response.status_code == 200
        mock_repo.git.rm.assert_called_with('-r', '--cached', '.', ignore_unmatch=True)
        assert not os.path.exists(os.path.join(repo_path, 'untracked.txt'))

    shutil.rmtree(workspace_root)
