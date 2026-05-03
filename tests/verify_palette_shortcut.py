import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import json

@pytest.fixture(scope="module")
def server():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })

    server_thread = threading.Thread(target=lambda: app.run(port=5006, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield "http://localhost:5006"

def test_keyboard_shortcut_focus(page: Page, server):
    # Mock user profile to avoid login form
    page.route("**/api/user", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            'login': 'testuser',
            'avatar_url': 'https://github.com/testuser.png'
        })
    ))
    page.route("**/api/repos", lambda route: route.fulfill(status=200, body="[]"))
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(status=200, body="[]"))
    page.route("**/api/tasks", lambda route: route.fulfill(status=200, body="[]"))

    page.goto(server)

    # 1. Test Dashboard Tab Search Focus
    page.click("#dashboard-tab")
    page.keyboard.press("/")
    expect(page.locator("#dashboardRepoSearch")).to_be_focused()

    # 2. Test Actions Tab Search Focus
    page.click("#actions-tab")
    page.keyboard.press("/")
    expect(page.locator("#runSearch")).to_be_focused()

    # 3. Test Workspace Tab Search Focus
    page.click("#workspace-tab")
    page.keyboard.press("/")
    expect(page.locator("#workspaceOmniSearch")).to_be_focused()

    # 4. Test Shortcut doesn't trigger when in an input
    page.locator("#workspaceOmniSearch").fill("test")
    page.keyboard.press("/")
    # It should type "/" instead of refocusing/preventing default
    expect(page.locator("#workspaceOmniSearch")).to_have_value("test/")
