
import pytest
from app import create_app
import json

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_xss_in_error_message(client):
    # Simulate a login
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'
        sess['session_id'] = 'test-session'

    # Trigger an error that might contain controlled input
    # Use a more direct way to trigger the error if clone fails with 415
    # The app uses URLSearchParams or FormData
    malicious_url = "https://github.com/owner/repo<img src=x onerror=alert(1)>"

    response = client.post('/api/workspace/clone', data={'repo_url': malicious_url})

    # GitPython might throw a GitCommandError if the URL is invalid, which returns 500
    # Let's see what happens.
    if response.status_code == 415:
         print("415 error, maybe it expects JSON?")
         response = client.post('/api/workspace/clone', json={'repo_url': malicious_url})

    assert response.status_code == 500
    data = response.get_json()
    assert "repo<img src=x onerror=alert(1)>" in data['error']
    print(f"\nResponse contains potential XSS: {data['error']}")
