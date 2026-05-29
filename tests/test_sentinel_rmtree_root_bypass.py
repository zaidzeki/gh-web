import pytest
from app import create_app
import os
import shutil

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
        'SESSION_COOKIE_SECURE': False
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_delete_workspace_root_bypass_repro(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['active_repo'] = 'test-repo-repro'
        sess['session_id'] = 'test-session-repro'

    # Ensure workspace exists
    workspace_dir = '/tmp/gh-web-workspaces/test-session-repro/test-repo-repro'
    sub_dir = os.path.join(workspace_dir, 'sub')
    os.makedirs(sub_dir, exist_ok=True)
    test_file = os.path.join(workspace_dir, 'important_root_file.txt')
    with open(test_file, 'w') as f:
        f.write('should not be deleted')

    try:
        # Try to delete root via 'sub/..'
        # The current check in routes.py is: if target_rel_path in ['.', './', '', '/']:
        # 'sub/..' is NOT in that list, so it proceeds to os.path.join(workspace_dir, 'sub/..')
        # which resolves to workspace_dir.
        response = client.delete('/api/workspace/files', json={'path': 'sub/..'})

        # If vulnerable, it might return 200 (but might also throw Errno 2 if shutil.rmtree('sub/..') fails as seen in my earlier repro)
        # But wait, in my earlier repro: shutil.rmtree('/tmp/test_rmtree_bypass/sub/..') FAILED with Errno 2,
        # but it ALREADY deleted everything INSIDE /tmp/test_rmtree_bypass except maybe some things?
        # Actually it deleted important.txt!

        assert os.path.exists(test_file), "Bypass successful! The root file was deleted even though we didn't specify '.', './', '', or '/'"

    finally:
        if os.path.exists('/tmp/gh-web-workspaces/test-session-repro'):
            shutil.rmtree('/tmp/gh-web-workspaces/test-session-repro')
