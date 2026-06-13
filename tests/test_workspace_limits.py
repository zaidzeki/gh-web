import os
import shutil
import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": "test-key"})
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_list_workspace_files_depth_limit(client, mocker):
    # Setup a mock workspace with deep structure
    repo_name = "test-repo-deep"
    session_id = "test-session-limits"
    workspace_base = "/tmp/gh-web-workspaces"
    workspace_dir = os.path.join(workspace_base, session_id, repo_name)

    os.makedirs(workspace_dir, mode=0o700, exist_ok=True)

    # Create a structure deeper than MAX_DEPTH (10)
    current_path = workspace_dir
    for i in range(15):
        current_path = os.path.join(current_path, f"depth_{i}")
        os.makedirs(current_path, exist_ok=True)
        with open(os.path.join(current_path, "file.txt"), "w") as f:
            f.write("test")

    try:
        with client.session_transaction() as sess:
            sess['github_token'] = 'test-token'
            sess['session_id'] = session_id
            sess['active_repo'] = repo_name

        response = client.get('/api/workspace/files')
        assert response.status_code == 200
        data = response.get_json()

        # Helper to find max depth in returned tree
        def get_max_depth(nodes, current_depth=0):
            if not nodes:
                return current_depth
            max_d = current_depth
            for node in nodes:
                if "children" in node:
                    max_d = max(max_d, get_max_depth(node["children"], current_depth + 1))
            return max_d

        returned_depth = get_max_depth(data)
        # MAX_DEPTH is 10, so it should not exceed 11 levels (root is 0)
        # Or if root is 0, depth 10 means 11 levels.
        # Let's check if it's <= 11
        assert returned_depth <= 11

    finally:
        if os.path.exists(os.path.join(workspace_base, session_id)):
            shutil.rmtree(os.path.join(workspace_base, session_id))

def test_list_workspace_files_item_limit(client, mocker):
    # Setup a mock workspace with many files
    repo_name = "test-repo-many"
    session_id = "test-session-limits-items"
    workspace_base = "/tmp/gh-web-workspaces"
    workspace_dir = os.path.join(workspace_base, session_id, repo_name)

    os.makedirs(workspace_dir, mode=0o700, exist_ok=True)

    # Create more than MAX_ITEMS (1000) files
    for i in range(1100):
        with open(os.path.join(workspace_dir, f"file_{i}.txt"), "w") as f:
            f.write("test")

    try:
        with client.session_transaction() as sess:
            sess['github_token'] = 'test-token'
            sess['session_id'] = session_id
            sess['active_repo'] = repo_name

        response = client.get('/api/workspace/files')
        assert response.status_code == 200
        data = response.get_json()

        # Count items in tree
        def count_items(nodes):
            count = 0
            for node in nodes:
                count += 1
                if "children" in node:
                    count += count_items(node["children"])
            return count

        total_items = count_items(data)
        # MAX_ITEMS is 1000. It stops listing once it reaches 1000.
        assert total_items <= 1000

    finally:
        if os.path.exists(os.path.join(workspace_base, session_id)):
            shutil.rmtree(os.path.join(workspace_base, session_id))

def test_download_repo_length_limits(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'

    # Test long repo name
    long_repo = "a" * 256
    response = client.post('/api/workspace/download', json={'repo_name': long_repo})
    assert response.status_code == 400
    assert "repo_name is too long" in response.get_json()['error']

    # Test long ref
    long_ref = "b" * 256
    response = client.post('/api/workspace/download', json={'repo_name': 'owner/repo', 'ref': long_ref})
    assert response.status_code == 400
    assert "ref is too long" in response.get_json()['error']
