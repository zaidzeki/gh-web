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

    server_thread = threading.Thread(target=lambda: app.run(port=5010, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield "http://localhost:5010"

    # Cleanup
    shutil.rmtree(template_path)

def test_modal_focus_file(page: Page, server):
    page.route("**/api/user", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({'login': 'testuser', 'avatar_url': 'https://github.com/testuser.png'})))
    page.route("**/api/repos", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))
    page.route("**/api/tasks", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))
    page.route("**/api/workspace/files", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([{'name': 'test.txt', 'path': 'test.txt', 'type': 'file'}])))
    page.route("**/api/workspace/files/content*", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({'content': 'hello world'})))
    page.route("**/api/workspace/status", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({'is_git': True, 'branch': 'main'})))
    page.route("**/api/workspace/portfolio", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))
    page.route("**/api/workspace/templates", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))

    page.goto(server)
    page.click("#workspace-tab")
    page.evaluate("window.refreshExplorer()")

    # Open file modal
    page.wait_for_selector("span[data-path='test.txt']")
    page.locator("span[data-path='test.txt']").click()

    # Wait for modal and check focus
    editor = page.locator("#fileContentEditor")
    expect(editor).to_be_focused()

def test_modal_focus_dispatch(page: Page, server):
    page.route("**/api/user", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({'login': 'testuser', 'avatar_url': 'https://github.com/testuser.png'})))
    page.route("**/api/repos", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))
    page.route("**/api/tasks", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))
    page.route("**/api/repos/**/actions/workflows", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([{'id': 1, 'name': 'Test WF', 'path': '.github/workflows/test.yml', 'state': 'active'}])))
    page.route("**/api/repos/**/actions/runs", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))
    page.route("**/api/workspace/templates", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))

    page.goto(server)
    page.click("#actions-tab")
    page.fill("#actionsRepoFullName", "test/repo")
    page.click("#listActionsBtn")

    # Open dispatch modal
    page.locator(".dispatch-wf-btn").first.click()

    # Check focus
    ref_input = page.locator("#dispatchRef")
    expect(ref_input).to_be_focused()

def test_modal_focus_publish_template(page: Page, server):
    page.route("**/api/workspace/templates", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(['test-template'])))

    page.goto(server)
    page.click("#templates-tab")

    # Open publish modal
    page.locator(".publish-template-btn").first.click()

    # Check focus
    repo_name_input = page.locator("#publishRepoName")
    expect(repo_name_input).to_be_focused()

def test_modal_focus_conversation(page: Page, server):
    page.route("**/api/user", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({'login': 'testuser', 'avatar_url': 'https://github.com/testuser.png'})))
    page.route("**/api/repos", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))
    page.route("**/api/tasks", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([{'type': 'issue', 'number': 1, 'repo': 'test/repo', 'title': 'Test Issue', 'updated_at': '2025-01-01T00:00:00Z', 'html_url': 'https://github.com/test/repo/issues/1', 'category': 'assigned'}])))
    page.route("**/api/repos/**/issues/**/comments", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))
    page.route("**/api/workspace/templates", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps([])))

    page.goto(server)
    # Wait for task inbox to load
    page.wait_for_selector(".comments-task-btn")
    page.click(".comments-task-btn")

    # Check focus
    comment_body = page.locator("#commentBody")
    expect(comment_body).to_be_focused()

def test_modal_focus_template_params(page: Page, server):
    page.route("**/api/workspace/templates", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(['test-template-focus'])))
    page.route("**/api/workspace/templates/*/manifest", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({'variables': [{'name': 'project_name', 'label': 'Project Name', 'default': 'my-project'}]})))

    page.goto(server)
    page.click("#repos-tab")
    page.select_option("#templateSelect", "test-template-focus")
    page.fill("#repoName", "test-repo")
    page.click("#createRepoForm button[type='submit']")

    # Check focus
    param_input = page.locator("#dynamicParamsContainer input")
    expect(param_input).to_be_focused()
