import pytest
from app import create_app
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_list_issues(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.issues.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_issue.title = 'Test Issue'
        mock_issue.state = 'open'
        mock_issue.html_url = 'http://github.com/owner/repo/issues/1'
        mock_issue.user.login = 'testuser'
        mock_issue.created_at = datetime(2023, 1, 1)
        mock_issue.pull_request = None # Important: filter out PRs

        mock_pr = MagicMock()
        mock_pr.pull_request = MagicMock() # Should be filtered out

        mock_repo.get_issues.return_value = [mock_issue, mock_pr]
        mock_github.return_value.get_repo.return_value = mock_repo

        response = client.get('/api/repos/owner/repo/issues')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['number'] == 1
        assert data[0]['title'] == 'Test Issue'

def test_create_issue(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.issues.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_issue.number = 2
        mock_issue.html_url = 'http://github.com/owner/repo/issues/2'
        mock_repo.create_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        response = client.get('/api/user') # Just to check auth if needed, but let's go straight to POST
        response = client.post('/api/repos/owner/repo/issues', json={'title': 'New Issue', 'body': 'Description'})

        assert response.status_code == 201
        data = response.get_json()
        assert data['number'] == 2
        assert 'Issue created successfully' in data['message']

def test_close_issue(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.issues.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        response = client.post('/api/repos/owner/repo/issues/1/close')

        assert response.status_code == 200
        data = response.get_json()
        assert 'closed successfully' in data['message']
        mock_issue.edit.assert_called_once_with(state='closed')
