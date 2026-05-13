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

@patch('git.Repo')
def test_branch_argument_injection(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    # Create dummy git dir
    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    # Attempt argument injection
    malicious_branch = '--help'
    response = client.post('/api/workspace/branch', json={
        'branch_name': malicious_branch,
        'create_new': False
    })

    # The new code should reject branch names starting with a dash
    assert response.status_code == 400
    assert "cannot start with a dash" in response.get_json()['error']
    mock_repo.git.checkout.assert_not_called()

@patch('git.Repo')
def test_branch_argument_injection_create(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    malicious_branch = '--version'
    response = client.post('/api/workspace/branch', json={
        'branch_name': malicious_branch,
        'create_new': True
    })

    assert response.status_code == 400
    assert "cannot start with a dash" in response.get_json()['error']
    mock_repo.git.checkout.assert_not_called()

@patch('git.Repo')
def test_branch_safe_with_dash_later(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['session_id'] = 'test_session'
        sess['active_repo'] = 'testrepo'

    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    safe_branch = 'feature-branch'
    response = client.post('/api/workspace/branch', json={
        'branch_name': safe_branch,
        'create_new': False
    })

    assert response.status_code == 200
    # Should use -- separator
    mock_repo.git.checkout.assert_called_with(safe_branch, '--')
