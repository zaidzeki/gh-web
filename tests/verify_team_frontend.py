import pytest
from playwright.sync_api import Page, expect
import time
import subprocess
import os

import threading
from app import create_app

@pytest.fixture(scope="module", autouse=True)
def server():
    app = create_app()
    app.config['SECRET_KEY'] = 'test-key'
    server_thread = threading.Thread(target=lambda: app.run(port=5001, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)
    yield

def test_team_context_switcher(page: Page):
    # Mocking the API responses for the frontend
    page.route("**/api/user", lambda route: route.fulfill(json={
        "login": "test-user",
        "avatar_url": "https://example.com/avatar.png"
    }))

    page.route("**/api/user/orgs", lambda route: route.fulfill(json=[
        {"login": "test-org", "avatar_url": "https://example.com/org.png"}
    ]))

    page.route("**/api/user/orgs/test-org/teams", lambda route: route.fulfill(json=[
        {"id": 123, "name": "Frontend Team", "slug": "frontend-team"}
    ]))

    page.route("**/api/repos*", lambda route: route.fulfill(json=[
        {"full_name": "test-org/repo-1", "name": "repo-1", "description": "Repo 1", "open_issues_count": 0, "open_prs_count": 0, "pushed_at": None, "private": False}
    ]))

    page.route("**/api/tasks*", lambda route: route.fulfill(json=[]))
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(json=[]))
    page.route("**/api/workspace/templates", lambda route: route.fulfill(json=[]))

    page.goto("http://localhost:5001")

    # Check if context switcher is visible
    expect(page.locator("#orgContextSwitcherContainer")).to_be_visible()

    # Click context switcher
    page.click("#orgContextSwitcher")

    # Check if Org and Team are in the list
    expect(page.get_by_role("link", name="test-org", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="↳ Frontend Team")).to_be_visible()

    # Select Team
    page.click("text=↳ Frontend Team")

    # Verify button text updated
    expect(page.locator("#orgContextSwitcher span")).to_have_text("test-org / Frontend Team")

    # Verify repos refresh call (this is implicitly verified by page.route if it wasn't called it would hang or fail if we asserted on specific calls)
    # Let's verify the repo list updated
    expect(page.locator("#dashboardRepoList")).to_contain_text("test-org/repo-1")
