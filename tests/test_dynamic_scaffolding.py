import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import shutil
import os
import json

@pytest.fixture(scope="module")
def server():
    # Setup test templates
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    if os.path.exists(templates_root):
        shutil.rmtree(templates_root)
    os.makedirs(templates_root, exist_ok=True)

    dynamic_template = os.path.join(templates_root, 'dynamic-test')
    os.makedirs(dynamic_template, exist_ok=True)

    manifest = {
        "variables": [
            {"name": "project_name", "label": "Project Name", "default": "hello-world"},
            {"name": "author", "label": "Author", "default": "Jules"}
        ]
    }
    with open(os.path.join(dynamic_template, 'manifest.json'), 'w') as f:
        json.dump(manifest, f)

    os.makedirs(os.path.join(dynamic_template, 'src/{{project_name}}'), exist_ok=True)
    with open(os.path.join(dynamic_template, 'src/{{project_name}}/info.txt'), 'w') as f:
        f.write("Project: {{project_name}}\nAuthor: {{author}}")

    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })
    server_thread = threading.Thread(target=lambda: app.run(port=5002, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield "http://localhost:5002"

def test_dynamic_scaffolding_flow(page: Page, server):
    page.goto(server)

    # Login (fake token)
    page.fill('input[name="token"]', 'fake_token')
    page.click('button:has-text("Login")')

    # Go to Workspace and Clone a dummy repo to have an active workspace
    page.click("#workspace-tab")
    # We need an active repo. Let's mock it in session via a direct call if possible,
    # but Playwright is external. Let's use the UI to "clone" which might fail but should set the session.
    # Actually, the easiest is to just use a test that mocks the backend state.
    # But this is an E2E test.

    # Let's try to "Apply Template" directly. It should fail with "No active repository"
    page.select_option("#workspaceTemplateSelect", "dynamic-test")
    page.click("#applyTemplateBtn")

    # Should show the modal
    expect(page.locator("#templateParamsModal")).to_be_visible()
    expect(page.locator('label:has-text("Project Name")')).to_be_visible()

    page.fill('input[name="project_name"]', 'my-dynamic-app')
    page.fill('input[name="author"]', 'Horizon')

    # Clicking "Apply" in modal
    page.click("#confirmTemplateBtn")

    # Since there's no active repo, it should show an error toast
    expect(page.locator(".toast.bg-danger")).to_contain_text("No active repository")
