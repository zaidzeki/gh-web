
import pytest
from app import create_app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_dispatch_workflow_validation(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    # Test ref length validation (standard: 255)
    long_ref = 'a' * 256
    response = client.post('/api/repos/owner/repo/actions/workflows/123/dispatch', json={
        'ref': long_ref
    })
    assert response.status_code == 400
    assert "Ref is too long" in response.get_json()['error']

    # Test ref leading dash (security standard: cannot start with dash)
    dash_ref = '-bad-ref'
    response = client.post('/api/repos/owner/repo/actions/workflows/123/dispatch', json={
        'ref': dash_ref
    })
    assert response.status_code == 400
    assert "Invalid ref" in response.get_json()['error']

    # Test invalid type
    response = client.post('/api/repos/owner/repo/actions/workflows/123/dispatch', json={
        'ref': 123
    })
    assert response.status_code == 400
    assert "Ref must be a string" in response.get_json()['error']
