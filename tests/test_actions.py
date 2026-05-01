import pytest
from unittest.mock import MagicMock, patch
from flask import session

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

@patch('app.actions.routes.Github')
def test_list_workflows(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_wf = MagicMock()
    mock_wf.id = 123
    mock_wf.name = "CI"
    mock_wf.state = "active"
    mock_wf.path = ".github/workflows/ci.yml"
    mock_wf.html_url = "http://github.com/wf"

    mock_repo.get_workflows.return_value = [mock_wf]
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.get('/api/repos/owner/repo/actions/workflows')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == "CI"
    assert data[0]['id'] == 123

@patch('app.actions.routes.Github')
def test_list_runs(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_run = MagicMock()
    mock_run.id = 456
    mock_run.name = "Build"
    mock_run.status = "completed"
    mock_run.conclusion = "success"
    mock_run.head_branch = "main"
    mock_run.head_sha = "abcdef"
    mock_run.html_url = "http://github.com/run"
    mock_run.updated_at = MagicMock()
    mock_run.updated_at.isoformat.return_value = "2023-01-01T00:00:00"
    mock_run.run_number = 1

    mock_repo.get_workflow_runs.return_value = [mock_run]
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.get('/api/repos/owner/repo/actions/runs')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == "Build"
    assert data[0]['conclusion'] == "success"

@patch('app.actions.routes.Github')
def test_dispatch_workflow(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_wf = MagicMock()
    mock_wf.create_dispatch.return_value = True

    mock_repo.get_workflow.return_value = mock_wf
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.post('/api/repos/owner/repo/actions/workflows/123/dispatch', json={'ref': 'main'})
    assert response.status_code == 200
    assert "dispatched successfully" in response.get_json()['message']
