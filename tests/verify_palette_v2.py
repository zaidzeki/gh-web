import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import os
import shutil
import tempfile
import json
import re

@pytest.fixture(scope="module")
def server():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })

    server_thread = threading.Thread(target=lambda: app.run(port=5005, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield "http://localhost:5005"

def test_dashboard_keyboard_accessibility(page: Page, server):
    # Mock API responses using Playwright
    page.route("**/api/user", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            'login': 'testuser',
            'avatar_url': 'https://github.com/testuser.png'
        })
    ))
    page.route("**/api/repos", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([{
            'full_name': 'test/repo1',
            'description': 'Test Repo 1',
            'html_url': 'https://github.com/test/repo1',
            'open_prs_count': 2
        }])
    ))
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([{
            'repo_name': 'test/repo1',
            'branch': 'main',
            'is_dirty': True,
            'untracked': False
        }])
    ))
    page.route("**/api/workspace/templates", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([])
    ))

    page.goto(server)

    # Wait for repos to load
    repo_item = page.locator("h6[data-repo='test/repo1']")
    expect(repo_item).to_be_visible(timeout=10000)

    # Check accessibility attributes
    expect(repo_item).to_have_attribute("tabindex", "0")
    expect(repo_item).to_have_attribute("role", "button")
    expect(repo_item).to_have_attribute("aria-label", re.compile(r"Open repository test/repo1"))

    # Check focus indicator
    repo_item.focus()
    expect(repo_item).to_be_focused()

    # Test keyboard interaction
    repo_item.press("Enter")
    # Should switch to PRs tab and fill repo name
    expect(page.locator("#prs-tab")).to_have_class(re.compile("active"))
    expect(page.locator("#repoFullName")).to_have_value("test/repo1")

def test_workspace_keyboard_accessibility(page: Page, server):
    # Mock API responses using Playwright
    page.route("**/api/user", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            'login': 'testuser',
            'avatar_url': 'https://github.com/testuser.png'
        })
    ))
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([{
            'repo_name': 'test/repo1',
            'branch': 'main',
            'is_dirty': True,
            'untracked': False
        }])
    ))
    page.route("**/api/workspace/templates", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([])
    ))
    page.route("**/api/workspace/activate", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({'message': 'Activated'})
    ))
    page.route("**/api/workspace/status", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({'is_git': False})
    ))
    page.route("**/api/workspace/files", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([])
    ))

    page.goto(server)

    # Wait for workspaces to load
    workspace_item = page.locator("h6[data-repo-name='test/repo1']")
    expect(workspace_item).to_be_visible(timeout=10000)

    # Check accessibility attributes
    expect(workspace_item).to_have_attribute("tabindex", "0")
    expect(workspace_item).to_have_attribute("role", "button")
    expect(workspace_item).to_have_attribute("aria-label", re.compile(r"Open workspace test/repo1"))

    # Check icon-only buttons
    sync_btn = page.locator(".sync-workspace-btn[data-repo-name='test/repo1']")
    expect(sync_btn).to_have_attribute("aria-label", "Sync workspace test/repo1")

    revert_btn = page.locator(".revert-workspace-btn[data-repo-name='test/repo1']")
    expect(revert_btn).to_have_attribute("aria-label", "Discard changes for workspace test/repo1")

    # Test keyboard interaction
    workspace_item.focus()
    workspace_item.press("Space")
    # Should switch to Workspace tab
    expect(page.locator("#workspace-tab")).to_have_class(re.compile("active"))
