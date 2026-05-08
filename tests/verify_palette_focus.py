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
    template_name = "test-template-focus"
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

    server_thread = threading.Thread(target=lambda: app.run(port=5004, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield "http://localhost:5004"

    # Cleanup
    shutil.rmtree(template_path)

def test_template_params_auto_focus(page: Page, server):
    page.goto(server)
    page.click("#templates-tab")

    # Go to Repos tab to trigger template params modal
    page.click("#repos-tab")
    page.select_option("#templateSelect", "test-template-focus")
    page.fill("#repoName", "test-repo")
    page.click("#createRepoForm button[type='submit']")

    # Modal should appear
    modal = page.locator("#templateParamsModal")
    expect(modal).to_be_visible()

    # Verify auto-focus on the first input in the dynamic params container
    input_field = modal.locator("#dynamicParamsContainer input").first
    expect(input_field).to_be_focused()

def test_file_modal_auto_focus(page: Page, server):
    page.goto(server)
    page.click("#workspace-tab")

    # We can't easily mock the workspace files here, but we can trigger the modal via JS
    page.evaluate('''() => {
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('fileModal'));
        modal.show();
    }''')

    # Verify auto-focus on the file content editor
    expect(page.locator("#fileContentEditor")).to_be_focused()

def test_dispatch_modal_auto_focus(page: Page, server):
    page.goto(server)
    page.evaluate('''() => {
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('dispatchModal'));
        modal.show();
    }''')

    # Verify auto-focus on the dispatch ref input
    expect(page.locator("#dispatchRef")).to_be_focused()

def test_publish_template_modal_auto_focus(page: Page, server):
    page.goto(server)
    page.evaluate('''() => {
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('publishTemplateModal'));
        modal.show();
    }''')

    # Verify auto-focus on the publish repo name input
    expect(page.locator("#publishRepoName")).to_be_focused()

def test_conversation_modal_auto_focus(page: Page, server):
    page.goto(server)
    page.evaluate('''() => {
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('conversationModal'));
        modal.show();
    }''')

    # Verify auto-focus on the comment body textarea
    expect(page.locator("#commentBody")).to_be_focused()
