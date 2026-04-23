
import os
import pytest
from app import create_app
from app.workspace.routes import get_workspace_dir

@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    return app

def test_get_workspace_dir_traversal(app):
    with app.test_request_context():
        from flask import session
        session['session_id'] = 'user1'

        # Malicious repo name
        malicious_name = '../../etc'
        path = get_workspace_dir(malicious_name)

        # In current implementation, this will likely be /tmp/gh-web-workspaces/etc
        # which is OUTSIDE of user1's directory.

        expected_prefix = os.path.join('/tmp/gh-web-workspaces', 'user1')
        normalized_path = os.path.normpath(path)
        normalized_expected = os.path.normpath(expected_prefix)

        print(f"Path: {normalized_path}")
        print(f"Expected prefix: {normalized_expected}")

        assert normalized_path.startswith(normalized_expected)
