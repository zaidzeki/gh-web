import pytest
from unittest.mock import MagicMock, patch
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

@patch('app.prs.routes.Github')
def test_list_prs(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_pr.number = 1
    mock_pr.title = "Test PR"
    mock_pr.state = "open"
    mock_pr.html_url = "http://example.com/pr/1"
    mock_pr.user.login = "testuser"
    mock_pr.head.repo.full_name = "owner/repo"
    mock_pr.head.ref = "feature"
    mock_repo.get_pulls.return_value = [mock_pr]
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.get('/api/repos/owner/repo/prs')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['title'] == "Test PR"
    assert data[0]['head_repo_full_name'] == "owner/repo"
    assert data[0]['head_branch'] == "feature"

@patch('app.prs.routes.Github')
def test_create_pr(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_pr.number = 2
    mock_pr.html_url = "http://example.com/pr/2"
    mock_repo.create_pull.return_value = mock_pr
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.post('/api/repos/owner/repo/prs', json={
        'title': 'New PR',
        'head': 'feature',
        'base': 'main'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['number'] == 2
    mock_repo.create_pull.assert_called_once_with(title='New PR', body='', head='feature', base='main')

@patch('app.prs.routes.Github')
def test_merge_pr(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_status = MagicMock()
    mock_status.merged = True
    mock_pr.merge.return_value = mock_status
    mock_repo.get_pull.return_value = mock_pr
    mock_github.return_value.get_repo.return_value = mock_repo

    response = client.post('/api/repos/owner/repo/prs/1/merge', json={
        'commit_message': 'Merging PR',
        'merge_method': 'squash'
    })
    assert response.status_code == 200
    assert response.get_json() == {"message": "Pull Request merged successfully"}
    mock_pr.merge.assert_called_once_with(commit_message='Merging PR', merge_method='squash')
