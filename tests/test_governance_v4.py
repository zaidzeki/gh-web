import pytest
import json
import datetime
from flask import session
from app import create_app
from unittest.mock import MagicMock, patch

@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test'})
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@patch('app.governance.routes.Github')
@patch('app.repos.routes.Github')
@patch('app.pulse.routes.Github')
def test_governance_v4_logic(mock_pulse_github, mock_repos_github, mock_gov_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    # Mock Repo and Alerts
    mock_repo = MagicMock()
    mock_repo.full_name = 'owner/repo'
    mock_gov_github.return_value.get_repo.return_value = mock_repo
    mock_repos_github.return_value.get_repo.return_value = mock_repo
    mock_pulse_github.return_value.get_repo.return_value = mock_repo

    # 1. Test SLA Violation Logic
    mock_alert = MagicMock()
    mock_alert.number = 123
    mock_alert.security_advisory.severity = 'critical'
    mock_alert.security_vulnerability.package.name = 'test-pkg'
    mock_alert.security_vulnerability.first_patched_version_identifier = '1.0.1'
    mock_alert.html_url = 'http://example.com'
    # 72 hours ago (violates 48h SLA)
    mock_alert.created_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=72)
    mock_repo.get_dependabot_alerts.return_value = [mock_alert]
    mock_repo.get_secret_scanning_alerts.return_value = []
    mock_repo.get_codescan_alerts.return_value = []
    mock_repo.get_combined_status.return_value.state = 'success'

    response = client.get('/api/repos/owner/repo/governance/policy')
    assert response.status_code == 200
    data = response.get_json()
    assert data['policies']['sla_violation'] == True
    assert data['compliant'] == False
    assert any("SLA Violation" in v['message'] for v in data['violations'])

    # 2. Test PATCH Override
    patch_response = client.patch('/api/repos/owner/repo/governance/policy',
                                 json={
                                     "block_merge_on_sla_violation": False,
                                     "block_merge_on_critical_security": False
                                 })
    assert patch_response.status_code == 200

    # Re-evaluate
    response = client.get('/api/repos/owner/repo/governance/policy')
    data = response.get_json()
    assert data['policies']['block_merge_on_sla_violation'] == False
    assert data['policies']['block_merge_on_critical_security'] == False
    assert data['compliant'] == True # Should be compliant now since we disabled blocking

    # 3. Test Heatmap Aggregation
    with patch('app.governance.routes.calculate_repo_pulse') as mock_calc_pulse:
        mock_calc_pulse.return_value = {
            "metrics": {
                "dependency_freshness_index": 90,
                "security_mttr_hours": 12
            }
        }

        heatmap_response = client.get('/api/workspace/portfolio/governance/heatmap?repos=owner/repo')
        assert heatmap_response.status_code == 200
        heatmap_data = heatmap_response.get_json()
        assert len(heatmap_data) == 1
        assert heatmap_data[0]['quadrant'] == 'Elite'
        assert heatmap_data[0]['x'] == 90
        assert heatmap_data[0]['y'] == 12
