import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time
import os

@pytest.fixture(scope="module")
def server():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })

    server_thread = threading.Thread(target=lambda: app.run(port=5003, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)
    yield "http://localhost:5003"

def test_copy_diff_button_exists(page: Page, server):
    page.goto(server)
    button = page.locator("#copyDiffBtn")
    expect(button).to_have_count(1)
    expect(button).to_have_text("Copy Diff")

def test_copy_diff_feedback(page: Page, server):
    page.goto(server)

    # Mock the clipboard API
    page.evaluate("navigator.clipboard.writeText = () => Promise.resolve()")

    # Mock the diff content
    page.evaluate("document.getElementById('diffContent').textContent = 'test diff content'")

    # Make the button visible by showing the modal
    page.evaluate("new bootstrap.Modal(document.getElementById('diffModal')).show()")

    # Click the button
    page.click("#copyDiffBtn")

    # Check for feedback text
    expect(page.locator("#copyDiffBtn")).to_have_text("Copied!")

    # Wait for it to revert
    page.wait_for_timeout(2500)
    expect(page.locator("#copyDiffBtn")).to_have_text("Copy Diff")
