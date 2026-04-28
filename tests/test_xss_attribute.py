
import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import socket
import json

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

@pytest.fixture(scope="module")
def server():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test', 'SESSION_COOKIE_SECURE': False})
    port = get_free_port()
    def run_app():
        app.run(port=port, debug=False, use_reloader=False)
    thread = threading.Thread(target=run_app)
    thread.daemon = True
    thread.start()
    time.sleep(1)
    yield f"http://127.0.0.1:{port}"

def test_xss_attribute_injection(server, page: Page):
    page.goto(server)

    # Mock an endpoint that returns a malicious repo name
    # We want to see if escapeHTML escapes double quotes
    malicious_name = 'myrepo" onmouseover="window.xss_attr_executed=true'
    mock_data = [{
        "full_name": malicious_name,
        "name": "malicious",
        "description": "test",
        "html_url": "http://github.com/malicious",
        "open_prs_count": 0,
        "stargazers_count": 0,
        "open_issues_count": 0,
        "pushed_at": "2023-01-01T00:00:00",
        "private": False
    }]

    page.route("**/api/repos", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(mock_data)
    ))

    # Trigger login (mocked)
    page.evaluate("""
        localStorage.setItem('github_token', 'fake-token');
    """)
    # We need to trigger the initial load or a refresh
    page.route("**/api/user", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"login": "testuser", "avatar_url": "http://avatar", "name": "Test User", "html_url": "http://github.com/testuser"})
    ))

    page.reload()

    # Wait for the repo list to be rendered
    page.wait_for_selector('#dashboardRepoList .list-group-item')

    # Hover over the element to trigger onmouseover
    page.hover(f'h6[data-repo^="myrepo"]')

    # Check if the script executed
    time.sleep(0.5)
    xss_executed = page.evaluate("window.xss_attr_executed || false")
    assert xss_executed is False, "XSS was executed via attribute injection!"
