import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import json
from flask import request, session
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="module")
def server():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test', 'SESSION_COOKIE_SECURE': False})

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

def test_context_switching(server, page: Page):
    # Setup Playwright mocking
    page.route("**/api/user", lambda route: route.fulfill(
        json={"login": "testuser", "avatar_url": "https://example.com/user.png"}
    ))

    page.route("**/api/user/orgs", lambda route: route.fulfill(
        json=[{"login": "testorg", "avatar_url": "https://example.com/org.png", "description": "Test Org"}]
    ))

    def handle_repos(route):
        url = route.request.url
        if "org_name=testorg" in url:
            route.fulfill(json=[{
                "full_name": "testorg/repo", "name": "repo", "description": "Org Repo",
                "html_url": "https://github.com/testorg/repo", "stargazers_count": 0,
                "open_issues_count": 0, "open_prs_count": 0, "pushed_at": "2025-01-01T00:00:00", "private": False
            }])
        else:
            route.fulfill(json=[{
                "full_name": "user/repo", "name": "repo", "description": "User Repo",
                "html_url": "https://github.com/user/repo", "stargazers_count": 0,
                "open_issues_count": 0, "open_prs_count": 0, "pushed_at": "2025-01-01T00:00:00", "private": False
            }])

    page.route("**/api/repos*", handle_repos)
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(json=[]))
    page.route("**/api/tasks", lambda route: route.fulfill(json=[]))
    page.route("**/api/workspace/templates", lambda route: route.fulfill(json=[]))

    page.goto(server)

    # Simulate being logged in
    page.evaluate("initDashboard()")

    # Wait for Personal repos to load
    expect(page.locator("#dashboardRepoList")).to_contain_text("user/repo")

    # Open context switcher
    page.click("#orgContextSwitcher")
    expect(page.locator("#orgContextList")).to_be_visible()
    expect(page.locator("#orgContextList")).to_contain_text("testorg")

    # Select testorg
    page.click('text="testorg"')

    # Wait for Org repos to load
    expect(page.locator("#dashboardRepoList")).to_contain_text("testorg/repo")
    expect(page.locator("#dashboardRepoList")).not_to_contain_text("user/repo")
    expect(page.locator("#orgContextSwitcher")).to_contain_text("testorg")

    # Switch back to Personal
    page.click("#orgContextSwitcher")
    page.click('#orgContextList a:has-text("Personal")')

    # Wait for Personal repos to load again
    expect(page.locator("#dashboardRepoList")).to_contain_text("user/repo")
    expect(page.locator("#orgContextSwitcher")).to_contain_text("Personal")
