import pytest
from unittest.mock import MagicMock
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

def test_list_releases(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.releases.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_release = MagicMock()
    mock_release.id = 123
    mock_release.tag_name = 'v1.0.0'
    mock_release.title = 'Release 1.0.0'
    mock_release.body = 'Notes'
    mock_release.draft = False
    mock_release.prerelease = False
    mock_release.html_url = 'http://github.com/release/123'
    mock_release.published_at = None

    mock_repo.get_releases.return_value = [mock_release]

    response = client.get('/api/repos/owner/repo/releases')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['tag_name'] == 'v1.0.0'

def test_generate_release_notes(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.releases.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_notes = MagicMock()
    mock_notes.name = 'Generated Name'
    mock_notes.body = 'Generated Body'
    mock_repo.generate_release_notes.return_value = mock_notes

    response = client.post('/api/repos/owner/repo/releases/generate-notes', json={
        'tag_name': 'v1.1.0'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Generated Name'
    assert data['body'] == 'Generated Body'

def test_create_release(client, mocker):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_g = mocker.patch('app.releases.routes.Github')
    mock_repo = MagicMock()
    mock_g.return_value.get_repo.return_value = mock_repo

    mock_release = MagicMock()
    mock_release.id = 456
    mock_release.html_url = 'http://github.com/release/456'
    mock_repo.create_git_release.return_value = mock_release

    response = client.post('/api/repos/owner/repo/releases', json={
        'tag_name': 'v2.0.0',
        'name': 'Version 2'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] == 456
    assert 'Release created successfully' in data['message']
