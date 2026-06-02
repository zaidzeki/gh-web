import pytest
from unittest.mock import MagicMock, patch
import datetime
from app import create_app

@pytest.fixture
def client():
    # Reset PolicyStore before each test
    import os
    from app.governance.routes import policy_store
    if os.path.exists(policy_store.storage_path):
        os.remove(policy_store.storage_path)
    policy_store._ensure_storage()

    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.governance.routes.Github')
def test_org_governance_api(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_org = MagicMock()
    mock_github.return_value.get_organization.return_value = mock_org
    mock_github.return_value.get_user.return_value.login = 'test-user'

    # 1. Get Org Policy (Default)
    response = client.get('/api/governance/orgs/acme-inc/policy')
    assert response.status_code == 200
    data = response.get_json()
    assert data['org'] == 'acme-inc'
    assert data['policies']['sla_critical_hours'] == 48

    # 2. Update Org Policy
    # Mock membership for PATCH
    mock_membership = MagicMock()
    mock_membership.role = 'admin'
    mock_org.get_membership.return_value = mock_membership

    response = client.patch('/api/governance/orgs/acme-inc/policy', json={
        "sla_critical_hours": 24,
        "block_merge_on_failing_ci": False
    })
    assert response.status_code == 200

    # 3. Verify effective policy for repo in that org
    mock_repo = MagicMock()
    mock_repo.full_name = 'acme-inc/app'
    mock_github.return_value.get_repo.return_value = mock_repo

    # We need to mock fetch_security_info used in evaluate_repo_policy
    with patch('app.governance.routes.fetch_security_info') as mock_fetch_sec:
        mock_fetch_sec.return_value = ({"vulnerabilities": {"critical": 0}, "secrets": {"open": 0}}, [])
        mock_repo.get_combined_status.return_value.state = 'success'

        response = client.get('/api/repos/acme-inc/app/governance/policy')
        assert response.status_code == 200
        data = response.get_json()
        assert data['policies']['sla_critical_hours'] == 24
        assert data['policies']['block_merge_on_failing_ci'] == False

@patch('app.tasks.routes.github.Github')
@patch('app.tasks.routes.policy_store')
def test_task_sla_enrichment(mock_policy_store, mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_user = MagicMock()
    mock_user.login = 'test-user'
    mock_github.return_value.get_user.return_value = mock_user

    # Mock security alert issue
    mock_alert = MagicMock()
    mock_alert.repository.full_name = 'owner/repo'
    mock_alert.number = 101
    mock_alert.title = 'Vulnerability in test-pkg'
    mock_alert.pull_request = None
    mock_alert.milestone = None
    # 10 hours ago
    now = datetime.datetime.now(datetime.timezone.utc)
    mock_alert.created_at = now - datetime.timedelta(hours=10)
    mock_alert.updated_at = now

    mock_github.return_value.search_issues.side_effect = [
        [], [], [], [], [mock_alert] # ActionRequired, InProgress, MyPRs, WaitingDeploy, Security
    ]

    mock_policy_store.get_effective_policy.return_value = {
        "sla_critical_hours": 12 # Tight SLA
    }

    response = client.get('/api/tasks?category=security_vulnerability')
    assert response.status_code == 200
    tasks = response.get_json()
    assert len(tasks) == 1
    task = tasks[0]
    assert task['sla_status'] == 'critical' # 12 - 10 = 2 hours left
    assert task['sla_remaining_hours'] == 2.0
