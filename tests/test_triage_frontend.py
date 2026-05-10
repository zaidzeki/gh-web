import pytest
import re
import threading
import time
import socket
from playwright.sync_api import Page, expect
from app import create_app

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

def test_triage_ui_elements(server, page: Page):
    # Mock user and repos
    page.route("**/api/user", lambda route: route.fulfill(
        json={"login": "testuser", "avatar_url": "https://github.com/testuser.png"}
    ))
    page.route("**/api/user/orgs", lambda route: route.fulfill(
        json=[]
    ))
    page.route("**/api/repos", lambda route: route.fulfill(
        json=[{
            "full_name": "owner/repo",
            "name": "repo",
            "description": "desc",
            "html_url": "https://github.com/owner/repo",
            "open_issues_count": 5,
            "open_prs_count": 2,
            "pushed_at": "2023-01-01T00:00:00Z",
            "private": False
        }]
    ))

    page.goto(server)

    # 1. Verify Dashboard Badges
    dashboard_repo = page.locator("#dashboardRepoList .list-group-item").first
    expect(dashboard_repo.locator(".badge:has-text('5 Issues')")).to_be_visible()
    expect(dashboard_repo.locator(".badge:has-text('2 PRs')")).to_be_visible()

    # 2. Verify Datalist and Autosuggest
    datalist = page.locator("#userReposList")
    expect(datalist.locator("option[value='owner/repo']")).to_be_attached()

    # 3. Verify Issues Tab state filters and labels
    page.click("#issues-tab")
    expect(page.locator("#issueStateOpen")).to_be_checked()
    expect(page.locator("#issueStateClosed")).to_be_visible()

    # Mock issues list with labels
    page.route("**/api/repos/owner/repo/issues?state=open", lambda route: route.fulfill(
        json=[{
            "number": 42,
            "title": "Bug in UI",
            "state": "open",
            "html_url": "url",
            "user": "user",
            "created_at": "2023-01-01T00:00:00Z",
            "labels": [{"name": "bug", "color": "ff0000"}]
        }]
    ))

    page.fill("#issuesRepoFullName", "owner/repo")
    page.click("#listIssuesBtn")

    issue_row = page.locator("#issuesTable tbody tr").first
    expect(issue_row.locator(".badge:has-text('bug')")).to_be_visible()
    expect(issue_row.locator(".close-issue-btn")).to_be_visible()
    expect(issue_row.locator(".fix-issue-btn")).to_be_visible()

    # 4. Verify PRs Tab state filters and labels
    page.click("#prs-tab")
    expect(page.locator("#prStateOpen")).to_be_checked()
    expect(page.locator("#prStateClosed")).to_be_visible()

    # Mock PRs list
    page.route("**/api/repos/owner/repo/prs?state=open", lambda route: route.fulfill(
        json=[{
            "number": 101,
            "title": "Add feature",
            "state": "open",
            "html_url": "url",
            "user": "user",
            "can_push": True,
            "labels": [{"name": "enhancement", "color": "00ff00"}]
        }]
    ))

    page.fill("#repoFullName", "owner/repo")
    page.click("#listPrsBtn")

    pr_row = page.locator("#prsTable tbody tr").first
    expect(pr_row.locator(".badge:has-text('enhancement')")).to_be_visible()
    expect(pr_row.locator(".close-pr-btn")).to_be_visible()
    expect(pr_row.locator(".merge-btn")).to_be_visible()
