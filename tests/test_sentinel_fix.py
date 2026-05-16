
import pytest
from app import create_app
import json

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_deployment_input_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    # Test ref length
    response = client.post('/api/repos/owner/repo/deployments', json={
        'ref': 'a' * 256,
        'environment': 'prod'
    })
    assert response.status_code == 400
    assert "Ref is too long" in response.get_json()['error']

    # Test environment length
    response = client.post('/api/repos/owner/repo/deployments', json={
        'ref': 'main',
        'environment': 'a' * 256
    })
    assert response.status_code == 400
    assert "Environment name is too long" in response.get_json()['error']

def test_release_input_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    # Test tag_name length
    response = client.post('/api/repos/owner/repo/releases', json={
        'tag_name': 'v' + '1' * 255,
        'name': 'Release'
    })
    assert response.status_code == 400
    assert "Tag name is too long" in response.get_json()['error']

def test_repo_input_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    # Test name length
    response = client.post('/api/repos', json={
        'name': 'a' * 101
    })
    assert response.status_code == 400
    assert "Repository name is too long" in response.get_json()['error']

def test_csp_headers(client):
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy', '')
    assert "object-src 'none';" in csp
    assert "frame-ancestors 'none';" in csp
    assert "form-action 'self';" in csp
