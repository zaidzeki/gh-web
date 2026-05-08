import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import json

@pytest.fixture(scope="module")
def server():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test', 'SESSION_COOKIE_SECURE': False})

    @app.route('/api/user_mock', methods=['GET'])
    def mock_user():
        return json.dumps({'login': 'testuser', 'avatar_url': 'http://example.com/avatar.png'}), 200

    @app.route('/api/user/orgs_mock', methods=['GET'])
    def mock_orgs():
        return json.dumps([{'login': 'test-org', 'avatar_url': 'http://example.com/org.png'}]), 200

    @app.route('/api/repos_mock', methods=['GET'])
    def mock_repos():
        return json.dumps([{'full_name': 'testuser/repo1', 'name': 'repo1', 'open_issues_count': 0, 'open_prs_count': 0}]), 200

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

def test_org_context_switcher_visibility(server, page: Page):
    # Intercept API calls to return our mocks
    page.route("**/api/user", lambda route: route.fulfill(json={'login': 'testuser', 'avatar_url': 'http://example.com/avatar.png'}))
    page.route("**/api/user/orgs", lambda route: route.fulfill(json=[{'login': 'test-org', 'avatar_url': 'http://example.com/org.png'}]))
    page.route("**/api/repos*", lambda route: route.fulfill(json=[{'full_name': 'testuser/repo1', 'name': 'repo1', 'open_issues_count': 0, 'open_prs_count': 0}]))
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(json=[]))
    page.route("**/api/tasks", lambda route: route.fulfill(json=[]))

    page.goto(server)

    # Wait for dashboard to init
    expect(page.locator("#orgContextSwitcherContainer")).to_be_visible()
    expect(page.locator("#orgContextSwitcher")).to_contain_text("Context: Personal")

    # Open dropdown
    page.locator("#orgContextSwitcher").click()
    expect(page.locator("#orgContextList")).to_be_visible()
    expect(page.locator("#orgContextList .dropdown-item[data-org='test-org']")).to_contain_text("test-org")

def test_context_switching_updates_header(server, page: Page):
    page.route("**/api/user", lambda route: route.fulfill(json={'login': 'testuser', 'avatar_url': 'http://example.com/avatar.png'}))
    page.route("**/api/user/orgs", lambda route: route.fulfill(json=[{'login': 'test-org', 'avatar_url': 'http://example.com/org.png'}]))
    page.route("**/api/repos*", lambda route: route.fulfill(json=[]))
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(json=[]))
    page.route("**/api/tasks", lambda route: route.fulfill(json=[]))

    page.goto(server)

    # Switch context
    page.locator("#orgContextSwitcher").click()
    page.locator("[data-org='test-org']").click()

    expect(page.locator("#orgContextSwitcher")).to_contain_text("Context: test-org")
    expect(page.locator("#repoListHeader")).to_contain_text("Repositories in test-org")

def test_keyboard_shortcut_focuses_search(server, page: Page):
    page.goto(server)

    # Press /
    page.keyboard.press("/")

    # Check if dashboard search is focused
    expect(page.locator("#dashboardRepoSearch")).to_be_focused()
