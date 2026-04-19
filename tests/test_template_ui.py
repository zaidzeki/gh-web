import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import shutil
import os

@pytest.fixture(scope="module")
def server():
    # Clean up templates for testing
    templates_root = os.path.expanduser('~/.zekiprod/templates')
    if os.path.exists(templates_root):
        shutil.rmtree(templates_root)
    os.makedirs(templates_root, exist_ok=True)

    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })
    server_thread = threading.Thread(target=lambda: app.run(port=5001, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield "http://localhost:5001"

def test_template_ui_elements(page: Page, server):
    page.goto(server)

    # Check "Save as Template" form in Workspace tab
    page.click("#workspace-tab")
    expect(page.locator("#saveTemplateForm")).to_be_visible()
    expect(page.locator("#templateName")).to_be_visible()
    expect(page.locator("button:has-text('Save Workspace as Template')")).to_be_visible()

    # Check "Template" select in Repositories tab
    page.click("#repos-tab")
    expect(page.locator("#templateSelect")).to_be_visible()
    # Should have only "None" option if no templates exist
    expect(page.locator("#templateSelect option")).to_have_count(1)
