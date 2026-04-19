import os
import pytest
from app.workspace.routes import is_safe_path

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
