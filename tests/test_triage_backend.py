import pytest
from app import create_app
from unittest.mock import MagicMock, patch
from datetime import datetime

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_list_issues_with_state_and_labels(client):
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
        mock_issue.pull_request = None

        mock_label = MagicMock()
        mock_label.name = 'bug'
        mock_label.color = 'ff0000'
        mock_issue.labels = [mock_label]

        mock_repo.get_issues.return_value = [mock_issue]
        mock_github.return_value.get_repo.return_value = mock_repo

        # Test state=open
        response = client.get('/api/repos/owner/repo/issues?state=open')
        assert response.status_code == 200, response.get_json()
        data = response.get_json()
        assert data[0]['labels'][0]['name'] == 'bug'
        mock_repo.get_issues.assert_called_with(state='open')

        # Test state=closed
        response = client.get('/api/repos/owner/repo/issues?state=closed')
        assert response.status_code == 200, response.get_json()
        mock_repo.get_issues.assert_called_with(state='closed')

def test_reopen_issue(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.issues.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        response = client.post('/api/repos/owner/repo/issues/1/reopen')

        assert response.status_code == 200, response.get_json()
        data = response.get_json()
        assert 'reopened successfully' in data['message']
        mock_issue.edit.assert_called_once_with(state='open')

def test_list_prs_with_state_and_labels(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.prs.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.number = 1
        mock_pr.title = 'Test PR'
        mock_pr.state = 'open'
        mock_pr.html_url = 'url'
        mock_pr.user.login = 'testuser'

        mock_head = MagicMock()
        mock_head.repo.full_name = 'owner/repo'
        mock_head.ref = 'feature'
        mock_head.repo.permissions.push = True
        mock_pr.head = mock_head

        mock_label = MagicMock()
        mock_label.name = 'enhancement'
        mock_label.color = '00ff00'
        mock_pr.labels = [mock_label]

        mock_repo.get_pulls.return_value = [mock_pr]
        mock_github.return_value.get_repo.return_value = mock_repo

        response = client.get('/api/repos/owner/repo/prs?state=closed')
        assert response.status_code == 200, response.get_json()
        data = response.get_json()
        assert data[0]['labels'][0]['name'] == 'enhancement'
        mock_repo.get_pulls.assert_called_with(state='closed')

def test_close_reopen_pr(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.prs.routes.get_github_client') as mock_github:
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo

        # Test close
        response = client.post('/api/repos/owner/repo/prs/1/close')
        assert response.status_code == 200, response.get_json()
        assert 'closed successfully' in response.get_json()['message']
        mock_pr.edit.assert_called_with(state='closed')

        # Test reopen
        response = client.post('/api/repos/owner/repo/prs/1/reopen')
        assert response.status_code == 200, response.get_json()
        assert 'reopened successfully' in response.get_json()['message']
        mock_pr.edit.assert_called_with(state='open')

def test_list_repos_distinct_counts(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    with patch('app.repos.routes.get_github_client') as mock_github:
        mock_user = MagicMock()
        mock_user.login = 'testuser'
        mock_repo = MagicMock()
        mock_repo.full_name = 'owner/repo'
        mock_repo.name = 'repo'
        mock_repo.description = 'desc'
        mock_repo.html_url = 'url'
        mock_repo.stargazers_count = 0
        mock_repo.pushed_at = None
        mock_repo.private = False

        mock_user.get_repos.return_value = [mock_repo]
        mock_github.return_value.get_user.return_value = mock_user

        # Mock search_issues for PRs and Issues
        mock_pr = MagicMock()
        mock_pr.repository.full_name = 'owner/repo'

        mock_issue = MagicMock()
        mock_issue.repository.full_name = 'owner/repo'

        def search_side_effect(query):
            if 'is:pr' in query:
                return [mock_pr, mock_pr] # 2 PRs
            if 'is:issue' in query:
                return [mock_issue] # 1 Issue
            return []

        mock_github.return_value.search_issues.side_effect = search_side_effect

        response = client.get('/api/repos')
        assert response.status_code == 200, response.get_json()
        data = response.get_json()
        assert data[0]['open_prs_count'] == 2
        assert data[0]['open_issues_count'] == 1
