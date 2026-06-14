import pytest
from app import create_app
import os
import shutil

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_repos_health_batch_limit(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    # Test limit of 50 repositories
    long_list = ",".join([f"owner/repo{i}" for i in range(51)])
    response = client.get(f'/api/repos/health?repos={long_list}')
    assert response.status_code == 400
    assert "Too many repositories requested" in response.get_json()['error']

    # Test repository name length limit
    long_name = "a" * 256
    response = client.get(f'/api/repos/health?repos={long_name}')
    assert response.status_code == 400
    assert "Repository name too long" in response.get_json()['error']

def test_login_token_limit(client):
    response = client.post('/login', data={'token': 'a' * 513})
    assert response.status_code == 400
    assert "Token is too long" in response.get_json()['error']

def test_workspace_portfolio_limit(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'
        sess['session_id'] = 'batch-test'

    workspace_root = '/tmp/gh-web-workspaces/batch-test'
    if os.path.exists(workspace_root):
        shutil.rmtree(workspace_root)
    os.makedirs(workspace_root)

    # Create 51 dummy repository directories
    for i in range(51):
        repo_dir = os.path.join(workspace_root, f'repo{i:02d}')
        os.makedirs(os.path.join(repo_dir, '.git'))

    # Mock git.Repo and other items to avoid actual git/github calls
    mocker.patch('git.Repo')
    mocker.patch('app.workspace.routes.get_repo_full_name_from_url', return_value='owner/repo')

    response = client.get('/api/workspace/portfolio')
    assert response.status_code == 200
    data = response.get_json()
    # Should only return the first 50
    assert len(data) == 50
    assert data[0]['repo_name'] == 'repo00'
    assert data[49]['repo_name'] == 'repo49'

    shutil.rmtree(workspace_root)

def test_milestone_portfolio_limit(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'
        sess['session_id'] = 'milestone-batch-test'

    workspace_root = '/tmp/gh-web-workspaces/milestone-batch-test'
    if os.path.exists(workspace_root):
        shutil.rmtree(workspace_root)
    os.makedirs(workspace_root)

    # Create 51 dummy repository directories
    for i in range(51):
        repo_dir = os.path.join(workspace_root, f'repo{i:02d}')
        os.makedirs(os.path.join(repo_dir, '.git'))

    # Mock git.Repo and GitHub client
    class MockRemote:
        def __init__(self, url):
            self.url = url

    class MockRemotes(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.origin = self.get('origin')
        def __getattr__(self, name):
            return self.get(name)

    def mock_repo_side_effect(path):
        m = mocker.Mock()
        m.remotes = MockRemotes({'origin': MockRemote('https://github.com/owner/repo')})
        return m

    mocker.patch('git.Repo', side_effect=mock_repo_side_effect)

    mocker.patch('app.milestones.routes.get_repo_full_name_from_url', return_value='owner/repo')
    mock_gh = mocker.patch('app.milestones.routes.Github')
    mock_repo = mock_gh.return_value.get_repo.return_value
    mock_repo.get_milestones.return_value = []

    response = client.get('/api/workspace/portfolio/milestones')
    assert response.status_code == 200
    # The limit is applied to the directories searched, so it shouldn't crash
    # and would have only called get_repo 50 times (though we mocked milestones to be empty)

    # Verify that it only processed 20 repos by checking call count of get_repo
    # (Portfolio aggregation in Phase 7 is capped at 20 repos)
    assert mock_gh.return_value.get_repo.call_count == 20

    shutil.rmtree(workspace_root)
