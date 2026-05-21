
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
    assert "connect-src 'self';" in csp
    assert "base-uri 'none';" in csp

def test_pr_merge_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    response = client.post('/api/repos/owner/repo/prs/1/merge', json={
        'commit_message': 'a' * 65537,
        'merge_method': 'merge'
    })
    assert response.status_code == 400
    assert "Commit message is too long" in response.get_json()['error']

def test_workspace_branch_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test-session'

    import os
    os.makedirs('/tmp/gh-web-workspaces/test-session/testrepo/.git', exist_ok=True)

    response = client.post('/api/workspace/branch', json={
        'branch_name': 'a' * 256
    })
    assert response.status_code == 400
    assert "Branch name is too long" in response.get_json()['error']

def test_save_template_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test-session'

    response = client.post('/api/workspace/save-template', json={
        'template_name': 'a' * 101
    })
    assert response.status_code == 400
    assert "Template name is too long" in response.get_json()['error']

def test_generate_release_notes_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    response = client.post('/api/repos/owner/repo/releases/generate-notes', json={
        'tag_name': 'a' * 256
    })
    assert response.status_code == 400
    assert "Tag name is too long" in response.get_json()['error']

def test_review_deployment_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    response = client.post('/api/repos/owner/repo/actions/runs/1/review', json={
        'event': 'approve',
        'comment': 'a' * 65537
    })
    assert response.status_code == 400
    assert "Comment is too long" in response.get_json()['error']
