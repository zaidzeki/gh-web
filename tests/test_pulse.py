import pytest
from datetime import datetime, timedelta, timezone
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

def test_calculate_repo_pulse_no_env(mocker):
    from app.pulse.routes import calculate_repo_pulse

    mock_g = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_environments.return_value = []
    mock_g.get_repo.return_value = mock_repo

    result = calculate_repo_pulse(mock_g, "owner/repo")
    assert result["metrics"]["deployment_frequency"] == 0
    assert "No production environment found" in result["info"]

def test_calculate_repo_pulse_success(mocker):
    from app.pulse.routes import calculate_repo_pulse

    mock_g = MagicMock()
    mock_repo = MagicMock()
    mock_repo.full_name = "owner/repo"

    # Mock environment
    mock_env = MagicMock()
    mock_env.name = "production"
    mock_repo.get_environments.return_value = [mock_env]

    # Mock deployments
    now = datetime.now(timezone.utc)

    # Current window deployments
    d1 = MagicMock()
    d1.id = 1
    d1.sha = "sha1"
    d1.created_at = now - timedelta(days=5)
    s1 = MagicMock()
    s1.state = "success"
    d1.get_statuses.return_value = [s1]

    d2 = MagicMock()
    d2.id = 2
    d2.sha = "sha2"
    d2.created_at = now - timedelta(days=2)
    s2 = MagicMock()
    s2.state = "failure"
    d2.get_statuses.return_value = [s2]

    d3 = MagicMock()
    d3.id = 3
    d3.sha = "sha3"
    d3.created_at = now - timedelta(days=1)
    s3 = MagicMock()
    s3.state = "success"
    d3.get_statuses.return_value = [s3]

    # Previous window deployments
    d4 = MagicMock()
    d4.id = 4
    d4.sha = "sha4"
    d4.created_at = now - timedelta(days=40)
    s4 = MagicMock()
    s4.state = "success"
    d4.get_statuses.return_value = [s4]

    mock_repo.get_deployments.return_value = [d3, d2, d1, d4]

    # Mock PRs
    mock_pr_issue = MagicMock()
    mock_pr_issue.number = 101
    mock_g.search_issues.return_value = [mock_pr_issue]

    mock_pr = MagicMock()
    mock_pr.merged_at = now - timedelta(days=6)
    mock_repo.get_pull.return_value = mock_pr

    mock_g.get_repo.return_value = mock_repo

    result = calculate_repo_pulse(mock_g, "owner/repo")

    # Current window metrics
    assert result["metrics"]["deployment_frequency"] == 2 # d1 and d3 are success
    assert result["metrics"]["change_failure_rate_percent"] == 33.33 # 1 failure out of 3
    assert result["metrics"]["time_to_restore_hours"] == 24.0 # d2(failure) to d3(success) = 1 day
    assert result["metrics"]["lead_time_to_change_hours"] == 24.0 # pr(merged -6d) to d1(success -5d) = 1 day

    # Previous window metrics
    assert result["previous_metrics"]["deployment_frequency"] == 1
    assert result["previous_metrics"]["change_failure_rate_percent"] == 0.0

    # Trends
    assert result["trends"]["deployment_frequency"] == "improving"
    assert result["trends"]["change_failure_rate_percent"] == "degrading"

    # Benchmarks
    assert "benchmarks" in result
    assert "overall" in result["benchmarks"]

def test_get_repo_pulse_unauthorized(client):
    response = client.get('/api/repos/owner/repo/pulse')
    assert response.status_code == 401

def test_get_repo_pulse_success(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_calculate = mocker.patch('app.pulse.routes.calculate_repo_pulse')
    mock_calculate.return_value = {
        "repo": "owner/repo",
        "metrics": {"deployment_frequency": 5}
    }

    response = client.get('/api/repos/owner/repo/pulse')
    assert response.status_code == 200
    assert response.json["metrics"]["deployment_frequency"] == 5

def test_get_portfolio_pulse_success(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_calculate = mocker.patch('app.pulse.routes.calculate_repo_pulse')
    mock_calculate.side_effect = [
        {"repo": "repo1", "metrics": {"deployment_frequency": 2, "lead_time_to_change_hours": 10, "change_failure_rate_percent": 0, "time_to_restore_hours": None}},
        {"repo": "repo2", "metrics": {"deployment_frequency": 4, "lead_time_to_change_hours": 20, "change_failure_rate_percent": 50, "time_to_restore_hours": 5}}
    ]

    response = client.get('/api/workspace/portfolio/pulse?repos=repo1,repo2')
    assert response.status_code == 200
    assert response.json["metrics"]["deployment_frequency"] == 6
    assert response.json["metrics"]["lead_time_to_change_hours"] == 15.0 # (10+20)/2
    assert response.json["metrics"]["change_failure_rate_percent"] == 25.0 # (0+50)/2
    assert response.json["metrics"]["time_to_restore_hours"] == 5.0
    assert response.json["metrics"]["repo_count"] == 2
