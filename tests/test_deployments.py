import pytest
from unittest.mock import MagicMock
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

def test_list_environments(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.deployments.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_env = MagicMock()
    mock_env.name = 'production'
    mock_env.html_url = 'http://github.com/env/prod'
    mock_env.created_at = None
    mock_env.updated_at = None

    mock_repo.get_environments.return_value = [mock_env]

    response = client.get('/api/repos/owner/repo/environments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'production'

def test_list_deployments(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.deployments.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_deployment = MagicMock()
    mock_deployment.id = 1
    mock_deployment.sha = 'abc1234'
    mock_deployment.ref = 'main'
    mock_deployment.environment = 'production'
    mock_deployment.description = 'Deploying'
    mock_deployment.created_at = None
    mock_deployment.updated_at = None
    mock_deployment.creator.login = 'user'

    mock_status = MagicMock()
    mock_status.state = 'success'
    mock_status.description = 'Deployed'
    mock_status.updated_at = None
    mock_deployment.get_statuses.return_value = [mock_status]

    mock_repo.get_deployments.return_value = [mock_deployment]

    response = client.get('/api/repos/owner/repo/deployments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 1
    assert data[0]['latest_status']['state'] == 'success'

def test_create_deployment(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.deployments.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_deployment = MagicMock()
    mock_deployment.id = 2
    mock_deployment.sha = 'def5678'
    mock_repo.create_deployment.return_value = mock_deployment

    response = client.post('/api/repos/owner/repo/deployments', json={
        'ref': 'main',
        'environment': 'production'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] == 2
    assert 'Deployment created successfully' in data['message']

def test_review_deployment(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.deployments.routes.Github')
    mock_requests = mocker.patch('requests.get')
    mock_post = mocker.patch('requests.post')

    # Mock fetching pending deployments
    mock_requests.return_value.status_code = 200
    mock_requests.return_value.json.return_value = [
        {'environment': {'id': 456, 'name': 'production'}}
    ]

    # Mock review submission
    mock_post.return_value.status_code = 200

    response = client.post('/api/repos/owner/repo/actions/runs/123/review', json={
        'event': 'approve',
        'comment': 'Good to go'
    })

    assert response.status_code == 200
    assert 'approved successfully' in response.get_json()['message']

    # Verify post payload
    args, kwargs = mock_post.call_args
    assert kwargs['json']['environment_ids'] == [456]
    assert kwargs['json']['state'] == 'approve'
