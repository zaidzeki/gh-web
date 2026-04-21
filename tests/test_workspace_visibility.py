import os
import pytest
from flask import session
import git
import shutil
from app import create_app

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

def test_workspace_diff(client, monkeypatch):
    # Setup: Mock session and workspace
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['active_repo'] = 'test-repo'
        sess['session_id'] = 'test_session'

    repo_path = '/tmp/gh-web-workspaces/test_session/test-repo'
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    os.makedirs(repo_path)

    repo = git.Repo.init(repo_path)
    with open(os.path.join(repo_path, 'file.txt'), 'w') as f:
        f.write('initial content')
    repo.index.add(['file.txt'])
    repo.index.commit('initial commit')

    # Modify file
    with open(os.path.join(repo_path, 'file.txt'), 'w') as f:
        f.write('modified content')

    response = client.get('/api/workspace/diff')
    assert response.status_code == 200
    data = response.get_json()
    assert 'diff' in data
    assert '-initial content' in data['diff']
    assert '+modified content' in data['diff']

    # Cleanup
    shutil.rmtree(repo_path)

def test_workspace_history(client, monkeypatch):
    # Setup
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['active_repo'] = 'test-repo-hist'
        sess['session_id'] = 'test_session_hist'

    repo_path = '/tmp/gh-web-workspaces/test_session_hist/test-repo-hist'
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    os.makedirs(repo_path)

    repo = git.Repo.init(repo_path)
    # Configure Git identity
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test User")
        cw.set_value("user", "email", "test@example.com")

    with open(os.path.join(repo_path, 'file.txt'), 'w') as f:
        f.write('content')
    repo.index.add(['file.txt'])
    repo.index.commit('first commit')

    with open(os.path.join(repo_path, 'file.txt'), 'w') as f:
        f.write('new content')
    repo.index.add(['file.txt'])
    repo.index.commit('second commit')

    response = client.get('/api/workspace/history')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]['message'] == 'second commit'
    assert data[1]['message'] == 'first commit'
    assert 'hash' in data[0]
    assert 'author' in data[0]
    assert 'date' in data[0]

    # Cleanup
    shutil.rmtree(repo_path)

def test_workspace_revert(client, monkeypatch):
    # Setup
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
        sess['active_repo'] = 'test-repo-revert'
        sess['session_id'] = 'test_session_revert'

    repo_path = '/tmp/gh-web-workspaces/test_session_revert/test-repo-revert'
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    os.makedirs(repo_path)

    repo = git.Repo.init(repo_path)
    with open(os.path.join(repo_path, 'file.txt'), 'w') as f:
        f.write('initial content')
    repo.index.add(['file.txt'])
    repo.index.commit('initial commit')

    # Modify and add untracked
    with open(os.path.join(repo_path, 'file.txt'), 'w') as f:
        f.write('dirty content')
    with open(os.path.join(repo_path, 'untracked.txt'), 'w') as f:
        f.write('untracked')

    response = client.post('/api/workspace/revert')
    assert response.status_code == 200

    # Verify revert
    with open(os.path.join(repo_path, 'file.txt'), 'r') as f:
        assert f.read() == 'initial content'
    assert not os.path.exists(os.path.join(repo_path, 'untracked.txt'))

    # Cleanup
    shutil.rmtree(repo_path)
