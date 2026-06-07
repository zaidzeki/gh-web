import pytest
from unittest.mock import MagicMock, patch
import datetime

@pytest.fixture
def client():
    from app import create_app
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['github_token'] = 'test-token'
        yield client

@patch('app.tasks.routes.github.Github')
@patch('app.tasks.routes.github.Auth')
def test_task_search_scoping(mock_auth, mock_github, client):
    mock_g = MagicMock()
    mock_github.return_value = mock_g

    mock_user = MagicMock()
    mock_user.login = "testuser"
    mock_g.get_user.return_value = mock_user

    # Mock search_issues to return empty list
    mock_g.search_issues.return_value = []

    # 1. Test without org_name
    client.get("/api/tasks")

    # Verify search queries
    # Expected 5 calls for: action_required, in_progress, my_prs, waiting_deployment, security_alerts
    assert mock_g.search_issues.call_count >= 5

    calls = [c[0][0] for c in mock_g.search_issues.call_args_list]

    # Verify that security alerts filter is now scoped
    security_call_default = [c for c in calls if "label:dependabot" in c][0]
    assert "user:testuser" in security_call_default

    # 2. Test with org_name
    mock_g.search_issues.reset_mock()
    client.get("/api/tasks?org_name=myorg")

    calls_org = [c[0][0] for c in mock_g.search_issues.call_args_list]

    # Verify if org:myorg is added to filters
    security_call = [c for c in calls_org if "label:dependabot" in c][0]
    assert "org:myorg" in security_call

    # Check if in_progress filter has org:myorg
    ip_call = [c for c in calls_org if "assignee:testuser" in c][0]
    assert "org:myorg" in ip_call

@patch('app.issues.routes.get_github_client')
def test_update_milestone_validation(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_repo = MagicMock()
    mock_github.return_value.get_repo.return_value = mock_repo

    # Test with non-integer milestone_number
    response = client.post('/api/repos/owner/repo/issues/1/milestone', json={'milestone_number': 'not-an-int'})

    # It should now return 400
    assert response.status_code == 400
    assert "Must be an integer" in response.get_json()['error']
