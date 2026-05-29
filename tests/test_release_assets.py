import pytest
from unittest.mock import MagicMock, patch
import os
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

@pytest.fixture
def mock_github(mocker):
    mock_g = mocker.patch('app.releases.routes.Github')
    mock_instance = mock_g.return_value
    return mock_instance

@pytest.fixture
def mock_get_workspace_dir(mocker):
    return mocker.patch('app.releases.routes.get_workspace_dir')

def test_list_release_assets(client, mock_github):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_repo = MagicMock()
    mock_release = MagicMock()
    mock_asset = MagicMock()

    mock_asset.id = 123
    mock_asset.name = "test-asset.zip"
    mock_asset.label = "Test Label"
    mock_asset.size = 1024
    mock_asset.download_count = 5
    mock_asset.created_at = MagicMock()
    mock_asset.created_at.isoformat.return_value = "2023-01-01T00:00:00"
    mock_asset.browser_download_url = "http://github.com/asset"

    mock_github.get_repo.return_value = mock_repo
    mock_repo.get_release.return_value = mock_release
    mock_release.get_assets.return_value = [mock_asset]

    response = client.get('/api/repos/owner/repo/releases/1/assets')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == "test-asset.zip"

def test_upload_release_asset_success(client, mock_github, mock_get_workspace_dir, tmp_path):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'
        sess['session_id'] = 'test-session'

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    asset_file = workspace / "test.zip"
    asset_file.write_text("fake-content")

    mock_get_workspace_dir.return_value = str(workspace)

    mock_repo = MagicMock()
    mock_release = MagicMock()
    mock_asset = MagicMock()

    mock_asset.id = 456
    mock_asset.name = "test.zip"
    mock_asset.browser_download_url = "http://github.com/test.zip"

    mock_github.get_repo.return_value = mock_repo
    mock_repo.get_release.return_value = mock_release
    mock_release.upload_asset.return_value = mock_asset

    response = client.post('/api/repos/owner/repo/releases/1/assets', data={
        'workspace_path': 'test.zip',
        'name': 'test.zip',
        'label': 'Test Label'
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == "Asset uploaded successfully"
    assert data['id'] == 456

    # Verify upload_asset was called with correct args
    mock_release.upload_asset.assert_called_once()
    args, kwargs = mock_release.upload_asset.call_args
    assert kwargs['name'] == 'test.zip'
    assert kwargs['label'] == 'Test Label'
    assert kwargs['path'] == str(asset_file)

def test_upload_release_asset_invalid_path(client, mock_github, mock_get_workspace_dir, tmp_path):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    mock_get_workspace_dir.return_value = str(workspace)

    # Attempt to upload a file that doesn't exist
    response = client.post('/api/repos/owner/repo/releases/1/assets', data={
        'workspace_path': 'nonexistent.zip'
    })

    assert response.status_code == 400
    assert "Invalid workspace file path" in response.get_json()['error']

def test_delete_release_asset(client, mock_github):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_repo = MagicMock()
    mock_asset = MagicMock()

    mock_github.get_repo.return_value = mock_repo
    mock_repo.get_release_asset.return_value = mock_asset

    response = client.delete('/api/repos/owner/repo/releases/assets/789')
    assert response.status_code == 200
    assert response.get_json()['message'] == "Asset deleted successfully"
    mock_asset.delete_asset.assert_called_once()

def test_list_releases_with_asset_count(client, mock_github):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    mock_repo = MagicMock()
    mock_release = MagicMock()

    mock_release.id = 1
    mock_release.tag_name = "v1.0"
    mock_release.title = "Release 1"
    mock_release.body = "Notes"
    mock_release.draft = False
    mock_release.prerelease = False
    mock_release.html_url = "url"
    mock_release.published_at = None

    # Mocking assets
    mock_asset = MagicMock()
    mock_release.assets = [mock_asset, mock_asset]

    mock_github.get_repo.return_value = mock_repo
    mock_repo.get_releases.return_value = [mock_release]

    response = client.get('/api/repos/owner/repo/releases')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['assets_count'] == 2
