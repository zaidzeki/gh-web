import pytest
import threading
import time
from app import create_app
from playwright.sync_api import expect

@pytest.fixture(scope="module")
def server():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })

    # Use port 5003 to avoid conflicts with other potential tests
    port = 5003
    server_thread = threading.Thread(target=lambda: app.run(port=port, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield f"http://127.0.0.1:{port}"

def test_promotion_and_redeploy_ui(page, server):
    # This test focuses on UI behavior: clicking Promote/Redeploy should open modal with correct values
    page.goto(server)

    # Mock some data in the browser via injection if needed, but here we can simulate a login
    # Actually, we can just inject the 'github_token' into session if we had a way,
    # but it's easier to mock the API responses using playwright's route.

    # Mock /api/user to simulate logged in state
    page.route("**/api/user", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"login": "testuser", "avatar_url": "https://example.com/avatar.png"}'
    ))

    # Mock /api/user/orgs
    page.route("**/api/user/orgs", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[]'
    ))

    # Mock /api/repos
    page.route("**/api/repos*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"full_name": "owner/repo", "name": "repo", "open_prs_count": 0, "open_issues_count": 0, "pushed_at": "2025-01-01T00:00:00Z"}]'
    ))

    # Mock /api/repos/owner/repo/environments
    page.route("**/api/repos/owner/repo/environments", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"name": "production", "latest_deployment": null}]'
    ))

    # Mock /api/repos/owner/repo/deployments
    page.route("**/api/repos/owner/repo/deployments", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": 1, "sha": "sha123456789", "ref": "v1.0.0", "environment": "staging", "creator": "testuser", "created_at": "2025-01-01T00:00:00Z", "latest_status": {"state": "success"}}]'
    ))

    page.reload()

    # Navigate to Environments tab
    page.click("#environments-tab")

    # Type repo name and refresh
    page.fill("#deploymentsRepoFullName", "owner/repo")
    page.click("#listDeploymentsBtn")

    # Wait for deployment list to populate
    page.wait_for_selector(".promote-dep-btn")

    # 1. Test Promote
    page.click(".promote-dep-btn")

    # Check if modal is visible and populated
    expect(page.locator("#deploymentModal")).to_be_visible()
    expect(page.locator("#deployRef")).to_have_value("sha123456789")
    expect(page.locator("#promotionIndicator")).to_be_visible()
    expect(page.locator("#promotionIndicator")).to_contain_text("Promoting deployment v1.0.0 from staging")

    # Close modal
    page.click("#deploymentModal .btn-close")
    page.wait_for_selector("#deploymentModal", state="hidden")

    # 2. Test Redeploy
    page.click(".redeploy-dep-btn")

    # Check if modal is visible and populated
    expect(page.locator("#deploymentModal")).to_be_visible()
    expect(page.locator("#deployRef")).to_have_value("sha123456789")
    expect(page.locator("#deployEnv")).to_have_value("staging")
    expect(page.locator("#promotionIndicator")).to_be_visible()
    expect(page.locator("#promotionIndicator")).to_contain_text("Redeploying v1.0.0 to staging")

    # 3. Test Fresh Deployment button clears indicator
    page.click("#deploymentModal .btn-close")
    page.wait_for_selector("#deploymentModal", state="hidden")

    page.click("#newDeploymentBtn")
    expect(page.locator("#promotionIndicator")).to_be_hidden()
