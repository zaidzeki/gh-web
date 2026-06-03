import pytest
from unittest.mock import MagicMock, patch
import os
from app import create_app

@pytest.fixture
def client():
    # Reset PolicyStore before each test
    from app.governance.routes import policy_store
    if os.path.exists(policy_store.storage_path):
        os.remove(policy_store.storage_path)
    policy_store._ensure_storage()

    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.governance.routes.Github')
@patch('app.governance.routes.fetch_security_info')
def test_policy_lineage_api(mock_fetch_sec, mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    # Mock Org and Repo
    mock_org = MagicMock()
    mock_github.return_value.get_organization.return_value = mock_org
    mock_github.return_value.get_user.return_value.login = 'test-user'

    mock_repo = MagicMock()
    mock_repo.full_name = 'acme/app'
    mock_github.return_value.get_repo.return_value = mock_repo

    mock_fetch_sec.return_value = ({"vulnerabilities": {"critical": 0}, "secrets": {"open": 0}}, [])
    mock_repo.get_combined_status.return_value.state = 'success'

    # 1. Check Global Lineage (Default)
    response = client.get('/api/repos/acme/app/governance/policy')
    assert response.status_code == 200
    data = response.get_json()
    assert data['sources']['sla_critical_hours'] == 'global'
    assert data['sources']['block_merge_on_failing_ci'] == 'global'

    # 2. Override at Org Level
    from app.governance.routes import policy_store
    policy_store.update_org_policy('acme', {'sla_critical_hours': 24})

    response = client.get('/api/repos/acme/app/governance/policy')
    assert response.status_code == 200
    data = response.get_json()
    assert data['policies']['sla_critical_hours'] == 24
    assert data['sources']['sla_critical_hours'] == 'org'
    assert data['sources']['block_merge_on_failing_ci'] == 'global'

    # 3. Override at Repo Level
    policy_store.update_repo_policy('acme/app', {'block_merge_on_failing_ci': False})

    response = client.get('/api/repos/acme/app/governance/policy')
    assert response.status_code == 200
    data = response.get_json()
    assert data['policies']['sla_critical_hours'] == 24
    assert data['sources']['sla_critical_hours'] == 'org'
    assert data['policies']['block_merge_on_failing_ci'] == False
    assert data['sources']['block_merge_on_failing_ci'] == 'repo'

    # 4. Check Org API Lineage
    response = client.get('/api/governance/orgs/acme/policy')
    assert response.status_code == 200
    data = response.get_json()
    assert data['policies']['sla_critical_hours'] == 24
    assert data['sources']['sla_critical_hours'] == 'org'
    assert data['sources']['block_merge_on_failing_ci'] == 'global'
