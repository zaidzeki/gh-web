import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import os
import shutil
import tempfile
import json

@pytest.fixture(scope="module")
def server():
    # Setup a temporary workspace
    workspace_dir = tempfile.mkdtemp()

    # Setup templates directory
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    os.makedirs(templates_root, exist_ok=True)
    template_name = "test-template-a11y"
    template_path = os.path.join(templates_root, template_name)
    os.makedirs(template_path, exist_ok=True)

    with open(os.path.join(template_path, "manifest.json"), "w") as f:
        json.dump({
            "variables": [
                {"name": "project_name", "label": "Project Name", "default": "my-project"}
            ]
        }, f)

    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })

    server_thread = threading.Thread(target=lambda: app.run(port=5003, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield "http://localhost:5003"

    # Cleanup
    shutil.rmtree(template_path)

def test_template_params_a11y(page: Page, server):
    page.goto(server)
    page.click("#templates-tab")

    # Verify the delete button has the correct aria-label and title
    delete_btn = page.locator(".delete-template-btn[data-template='test-template-a11y']")
    expect(delete_btn).to_have_attribute("aria-label", "Delete template test-template-a11y")
    expect(delete_btn).to_have_attribute("title", "Delete template test-template-a11y")

    # Go to Repos tab to trigger template params modal
    page.click("#repos-tab")
    page.select_option("#templateSelect", "test-template-a11y")
    page.fill("#repoName", "test-repo")
    page.click("#createRepoForm button[type='submit']")

    # Modal should appear
    modal = page.locator("#templateParamsModal")
    expect(modal).to_be_visible()

    # Check id/for association
    label = modal.locator("label.form-label")
    expect(label).to_have_attribute("for", "param-project_name")
    input_field = modal.locator("input#param-project_name")
    expect(input_field).to_be_visible()
    expect(input_field).to_have_attribute("name", "project_name")
