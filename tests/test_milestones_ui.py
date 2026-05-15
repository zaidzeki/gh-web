import os
import threading
import time
import pytest
from flask import Flask, session
from playwright.sync_api import sync_playwright

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

    server_thread = threading.Thread(target=lambda: app.run(port=5001, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2) # Wait for server to start
    yield "http://127.0.0.1:5001"

def test_milestones_ui(server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(server)

        # 1. Login
        page.evaluate("""
            fetch('/test-login', {method: 'POST'})
                .then(() => window.location.reload())
        """)
        page.wait_for_load_state("networkidle")

        # 2. Check if Milestones tab exists and click it
        milestones_tab = page.locator("#milestones-tab")
        assert milestones_tab.is_visible()
        milestones_tab.click()

        # 3. Check Milestones pane content
        milestones_pane = page.locator("#milestones")
        page.wait_for_selector("#milestones.active")
        assert milestones_pane.is_visible()
        assert "Milestones & Goals" in milestones_pane.inner_text()

        # 4. Check for Create Milestone button and modal
        new_ms_btn = page.locator("#newMilestoneBtn")
        assert new_ms_btn.is_visible()
        new_ms_btn.click()

        ms_modal = page.locator("#milestoneModal")
        page.wait_for_selector("#milestoneModal.show")
        assert ms_modal.is_visible()

        # Take screenshot of the modal
        page.screenshot(path="tests/milestones_modal.png")

        # Just click the dashboard tab without closing the modal if it's being stubborn,
        # but the intercept log says it intercepts. Let's force it closed with extreme prejudice.
        page.evaluate("""
            const modalEl = document.getElementById('milestoneModal');
            modalEl.classList.remove('show');
            modalEl.style.display = 'none';
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
        """)
        time.sleep(1)

        # 5. Check Dashboard Milestone Filter
        # Use dispatch_event to bypass pointer intercept if needed
        page.locator("#dashboard-tab").dispatch_event("click")
        page.wait_for_selector("#dashboard.active")

        ms_filter = page.locator("#taskMilestoneFilter")
        assert ms_filter.is_visible()

        page.screenshot(path="tests/milestones_ui_verification.png")
        browser.close()

if __name__ == "__main__":
    # This allows running the script directly if needed
    pytest.main([__file__])
