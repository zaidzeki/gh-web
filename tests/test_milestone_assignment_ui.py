import os
import threading
import time
import pytest
from flask import Flask, session, jsonify
from playwright.sync_api import sync_playwright
from unittest.mock import MagicMock, patch

# Import the app factory
from app import create_app

@pytest.fixture(scope="module")
def server():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})

    # Simple login route for testing
    @app.route('/test-login', methods=['POST'])
    def test_login():
        session['github_token'] = 'fake-token'
        return {"message": "Logged in"}, 200

    server_thread = threading.Thread(target=lambda: app.run(port=5002, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2) # Wait for server to start
    yield "http://127.0.0.1:5002"

def test_milestone_assignment_ui(server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mocking user profile to avoid 500
        page.route("**/api/user", lambda route: route.fulfill(
            status=200,
            body='{"login": "testuser", "avatar_url": "http://example.com/avatar.png"}'
        ))

        # Mocking milestones API response
        page.route("**/api/repos/test/repo/milestones", lambda route: route.fulfill(
            status=200,
            body='[{"number": 1, "title": "v1.0", "open_issues": 1, "closed_issues": 0, "state": "open"}]'
        ))

        # Mocking issues API response
        page.route("**/api/repos/test/repo/issues?state=open", lambda route: route.fulfill(
            status=200,
            body='[{"number": 123, "title": "Issue 1", "state": "open", "html_url": "http://github.com", "user": "user1", "created_at": "2023-01-01T00:00:00Z", "labels": []}]'
        ))

        page.goto(server)

        # 1. Login
        page.evaluate("""
            fetch('/test-login', {method: 'POST'})
                .then(() => window.location.reload())
        """)
        page.wait_for_load_state("networkidle")

        # 2. Go to Issues tab
        issues_tab = page.locator("#issues-tab")
        issues_tab.click()

        # 3. List issues
        page.fill("#issuesRepoFullName", "test/repo")
        page.click("#listIssuesBtn")
        page.wait_for_selector("#issuesTable tbody tr")

        # 4. Check for Assign button
        assign_btn = page.locator(".assign-issue-milestone-btn").first
        assert assign_btn.is_visible()

        # 5. Click Assign button and check modal
        assign_btn.click()
        page.wait_for_selector("#assignMilestoneModal.show")

        modal = page.locator("#assignMilestoneModal")
        assert modal.is_visible()

        # Check if hidden fields are populated
        repo_val = page.evaluate("document.getElementById('assignMilestoneRepo').value")
        num_val = page.evaluate("document.getElementById('assignMilestoneNumber').value")
        assert repo_val == "test/repo"
        assert num_val == "123"

        # Check if milestone select is populated
        # option might be hidden by bootstrap modal but should be in DOM
        page.wait_for_selector("#milestoneSelect option[value='1']", state="attached")
        options_count = page.evaluate("document.querySelectorAll('#milestoneSelect option').length")
        assert options_count >= 2 # "No Milestone" + "v1.0"

        # 6. Test submission
        page.select_option("#milestoneSelect", "1")

        # Mock the assignment POST
        page.route("**/api/repos/test/repo/issues/123/milestone", lambda route: route.fulfill(
            status=200,
            body='{"message": "Milestone updated"}'
        ))

        page.click("#confirmAssignMilestoneBtn")

        # Modal should hide
        page.wait_for_selector("#assignMilestoneModal", state="hidden")

        browser.close()

if __name__ == "__main__":
    pytest.main([__file__])
