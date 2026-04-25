
import pytest
from app import create_app
from unittest.mock import MagicMock, patch

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_token_leakage_in_push(client):
    # Simulate a login with a sensitive token
    sensitive_token = "ghp_VERY_SECRET_TOKEN_12345"
    with client.session_transaction() as sess:
        sess['github_token'] = sensitive_token
        sess['active_repo'] = 'test-repo'
        sess['session_id'] = 'test-session'

    # Mock git.Repo and its push behavior
    with patch('git.Repo') as mock_repo_class, \
         patch('os.makedirs') as mock_makedirs:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Mock workspace directory existence
        with patch('os.path.exists', return_value=True):
            # Mock remote
            mock_remote = MagicMock()
            mock_remote.url = "https://github.com/user/test-repo.git"
            mock_repo.remote.return_value = mock_remote

            # Simulate a push failure that includes the URL with token
            mock_remote.push.side_effect = Exception(f"fatal: Authentication failed for 'https://{sensitive_token}@github.com/user/test-repo.git/'")

            response = client.post('/api/workspace/push')

            assert response.status_code == 500
            data = response.get_json()
            # This is expected to FAIL before the fix
            assert sensitive_token not in data['error']
            assert "********" in data['error']
