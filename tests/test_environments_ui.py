import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import json
import socket

@pytest.fixture(scope="module")
def server():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test', 'SESSION_COOKIE_SECURE': False})

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

def setup_mocks(page: Page):
    page.route("**/api/user", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            "login": "testuser",
            "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
            "name": "Test User",
            "html_url": "https://github.com/testuser"
        })
    ))
    page.route("**/api/repos", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([{
            "full_name": "testuser/testrepo",
            "name": "testrepo",
            "description": "test desc",
            "html_url": "https://github.com/testuser/testrepo",
            "stargazers_count": 0,
            "open_issues_count": 0,
            "open_prs_count": 0,
            "pushed_at": "2023-01-01T00:00:00Z",
            "private": False
        }])
    ))
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(status=200, body="[]"))
    page.route("**/api/tasks", lambda route: route.fulfill(status=200, body="[]"))
    page.route("**/api/workspace/templates", lambda route: route.fulfill(status=200, body="[]"))

    page.route("**/api/repos/testuser/testrepo/environments", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([{
            "id": 1,
            "name": "production",
            "html_url": "https://github.com/testuser/testrepo/deployments/production",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }])
    ))

    page.route("**/api/repos/testuser/testrepo/deployments*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([{
            "id": 100,
            "sha": "abcdef123456",
            "ref": "main",
            "task": "deploy",
            "environment": "production",
            "description": "Initial deploy",
            "creator": "testuser",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "status": "success"
        }])
    ))

def test_environments_tab(server, page: Page):
    setup_mocks(page)
    page.goto(server)

    # Check if Environments tab exists
    expect(page.locator("#environments-tab")).to_be_visible()

    # Click Environments tab
    page.click("#environments-tab")

    # Check if tab pane is visible
    expect(page.locator("#environments")).to_have_class("tab-pane fade active show")

    # Check for core elements
    expect(page.locator("#environmentsContainer")).to_be_visible()
    expect(page.locator("#deploymentsTable")).to_be_visible()
    expect(page.locator("#triggerDeployBtn")).to_be_visible()

def test_environments_quick_action(server, page: Page):
    setup_mocks(page)
    page.goto(server)

    # Wait for dashboard repo list to load
    page.wait_for_selector(".environments-action")

    # Click "Envs" quick action
    page.click(".environments-action")

    # Should switch to Environments tab and fill the repo name
    expect(page.locator("#environments-tab")).to_have_class("nav-link active")
    expect(page.locator("#environmentsRepoFullName")).to_have_value("testuser/testrepo")

    # Should load environments cards
    expect(page.locator(".card-title:has-text('production')")).to_be_visible()
    expect(page.locator("#environmentsContainer .badge:has-text('SUCCESS')")).to_be_visible()

def test_new_deployment_modal(server, page: Page):
    setup_mocks(page)
    page.goto(server)
    page.click("#environments-tab")
    page.click("#triggerDeployBtn")

    expect(page.locator("#deployModal")).to_be_visible()
    expect(page.locator("#deployRef")).to_be_visible()
    expect(page.locator("#deployEnv")).to_be_visible()
    expect(page.locator("#confirmDeployBtn")).to_be_visible()
