import pytest
from playwright.sync_api import Page, expect
import threading
from app import create_app
import time

@pytest.fixture(scope="module")
def server():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test'})
    import socket
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

def test_frontend_renders(server, page: Page):
    page.goto(server)
    expect(page.locator("a.navbar-brand")).to_contain_text("GH-Web")
    expect(page.locator("#mainTabs")).to_be_visible()
    expect(page.locator("#repos-tab")).to_be_visible()
