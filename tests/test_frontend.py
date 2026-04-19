import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import json
from flask import request

@pytest.fixture(scope="module")
def server():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test', 'SESSION_COOKIE_SECURE': False})

    # Mocking the login route to take some time
    @app.route('/login_mock', methods=['POST'])
    def mock_login():
        time.sleep(2.0)
        return json.dumps({'message': 'Logged in'}), 200

    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()

    def run_app():
        app.run(port=port, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_app)
    thread.daemon = True
    thread.start()
    time.sleep(1)
    yield f"http://127.0.0.1:{port}"

def test_frontend_renders(server, page: Page):
    page.goto(server)
    expect(page.locator("a.navbar-brand")).to_contain_text("GH-Web")
    expect(page.locator("#mainTabs")).to_be_visible()
    expect(page.locator("#repos-tab")).to_be_visible()

def test_loading_state(server, page: Page):
    page.goto(server)

    # Inject a form that uses the mock endpoint
    page.evaluate("""
        const form = document.createElement('form');
        form.id = 'mockForm';
        form.innerHTML = '<button type="submit">Submit</button>';
        document.body.appendChild(form);
        window.handleForm('mockForm', '/login_mock');
    """)

    submit_btn = page.locator('#mockForm button[type="submit"]')

    # Click it
    submit_btn.click()

    # Check for disabled state
    expect(submit_btn).to_be_disabled(timeout=1000)
    expect(submit_btn.locator('.spinner-border')).to_be_visible()

    # Wait for it to become enabled again
    expect(submit_btn).to_be_enabled(timeout=5000)
    expect(submit_btn.locator('.spinner-border')).not_to_be_visible()
