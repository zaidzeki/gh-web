
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

def test_xss_in_alert(server, page: Page):
    page.goto(server)

    # Mock an endpoint that returns a malicious error
    malicious_payload = '<img src=x onerror="window.xss_alert_executed=true">'
    page.route("**/api/xss-test", lambda route: route.fulfill(
        status=400,
        content_type="application/json",
        body=json.dumps({"error": malicious_payload})
    ))

    # Inject a form and use handleForm which is exposed
    page.evaluate("""
        const form = document.createElement('form');
        form.id = 'xssForm';
        form.innerHTML = '<button type="submit">Submit</button>';
        document.body.appendChild(form);
        window.handleForm('xssForm', '/api/xss-test');
    """)

    page.click('#xssForm button[type="submit"]')

    # Wait for the error alert to appear
    page.wait_for_selector('.alert-danger')

    # Check if the script executed
    xss_executed = page.evaluate("window.xss_alert_executed || false")
    assert xss_executed is False, "XSS was executed in showAlert!"
    print("\nXSS blocked in showAlert!")

def test_xss_in_render_tree(server, page: Page):
    page.goto(server)

    # Login first to enable workspace tab logic if needed
    page.fill('input[name="token"]', 'fake-token')
    page.click('#loginForm button[type="submit"]')
    time.sleep(0.5)

    # Go to Workspace tab
    page.click('#workspace-tab')

    # Mock the API response for /api/workspace/files
    # Use double escaping for the payload in JSON string
    malicious_name = '<img src=x onerror="window.xss_tree_executed=true">'
    mock_data = [{"name": malicious_name, "path": "malicious.txt", "type": "file"}]

    page.route("**/api/workspace/files", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(mock_data)
    ))

    # Refresh explorer
    page.click('#refreshExplorerBtn')

    # Wait for the element to appear in explorer
    page.wait_for_selector('#workspaceExplorer ul')

    # Check if the script executed
    time.sleep(1)
    xss_executed = page.evaluate("window.xss_tree_executed || false")
    assert xss_executed is False, "XSS was executed in renderTree!"
    print("\nXSS blocked in renderTree!")
