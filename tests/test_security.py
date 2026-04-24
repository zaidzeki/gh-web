import os
import pytest
from app import create_app
from app.workspace.routes import is_safe_path

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_is_safe_path_boundaries():
    basedir = "/tmp/gh-web-workspaces/session1/repo"

    # Normal safe paths
    assert is_safe_path(basedir, "/tmp/gh-web-workspaces/session1/repo/file.txt") is True
    assert is_safe_path(basedir, "/tmp/gh-web-workspaces/session1/repo/subdir/file.txt") is True

    # Common prefix attack (Sibling directory)
    # "/tmp/gh-web-workspaces/session1/repo-secret" starts with "/tmp/gh-web-workspaces/session1/repo"
    # but it's not inside it.
    assert is_safe_path(basedir, "/tmp/gh-web-workspaces/session1/repo-secret/file.txt") is False

    # Path traversal attack
    assert is_safe_path(basedir, "/tmp/gh-web-workspaces/session1/repo/../repo-secret/file.txt") is False
    assert is_safe_path(basedir, "/etc/passwd") is False

def test_is_safe_path_normalization():
    basedir = "/tmp/gh-web-workspaces/session1/repo/"
    # Normalization should handle trailing slashes
    assert is_safe_path(basedir, "/tmp/gh-web-workspaces/session1/repo/file.txt") is True
    assert is_safe_path("/tmp/gh-web-workspaces/session1/repo", "/tmp/gh-web-workspaces/session1/repo/") is True

def test_is_safe_path_relative():
    # is_safe_path uses realpath/abspath, so it should handle relative paths if the CWD is known
    # but typically it's called with absolute paths in this app.
    # Let's test with absolute paths as they are most critical.
    basedir = os.path.abspath("test_workspace")
    os.makedirs(basedir, exist_ok=True)
    try:
        safe_path = os.path.join(basedir, "file.txt")
        unsafe_path = os.path.join(basedir, "..", "outside.txt")

        assert is_safe_path(basedir, safe_path) is True
        assert is_safe_path(basedir, unsafe_path) is False
    finally:
        if os.path.exists(basedir):
            import shutil
            shutil.rmtree(basedir)

def test_list_files_no_symlink_traversal(client):
    """Verify that the file explorer does not follow symlinks to external directories."""
    import shutil
    session_id = "security-test-session"
    repo_name = "security-test-repo"
    workspace_dir = f"/tmp/gh-web-workspaces/{session_id}/{repo_name}"

    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    os.makedirs(workspace_dir)

    try:
        # Create a symlink to an external directory
        target_dir = "/etc"
        link_name = "external-link"
        link_path = os.path.join(workspace_dir, link_name)
        os.symlink(target_dir, link_path)

        # Create a normal file
        with open(os.path.join(workspace_dir, "normal.txt"), "w") as f:
            f.write("test")

        with client.session_transaction() as sess:
            sess['github_token'] = 'fake-token'
            sess['active_repo'] = repo_name
            sess['session_id'] = session_id

        response = client.get('/api/workspace/files')
        assert response.status_code == 200
        data = response.get_json()

        # The external-link should NOT be present because it points outside
        # OR it should be treated as a file, not followed as a directory.
        link_node = next((node for node in data if node['name'] == link_name), None)

        # In our fix, we skip it if it's not safe, or treat it as a file if it is safe but a link.
        # Since /etc is NOT safe (it's outside basedir), it should be skipped.
        assert link_node is None, "External symlink should not be listed in workspace"

        # Normal file should still be there
        assert any(node['name'] == 'normal.txt' for node in data)

    finally:
        if os.path.exists(workspace_dir):
            shutil.rmtree(workspace_dir)
