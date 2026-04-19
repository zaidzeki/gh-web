import pytest
from unittest.mock import MagicMock, patch
from app import create_app
import os
import io
import shutil
import tarfile

@pytest.fixture
def app_inst():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })
    yield app

@pytest.fixture
def client(app_inst):
    return app_inst.test_client()

def test_app_init_no_config():
    app = create_app()
    assert app.config['SECRET_KEY'] == 'dev'

def test_login_no_token(client):
    response = client.post('/login', data={})
    assert response.status_code == 400

@patch('app.repos.routes.Github')
def test_create_repo_error(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
    mock_github.return_value.get_user.side_effect = Exception("API Error")
    response = client.post('/api/repos', json={'name': 'test'})
    assert response.status_code == 500

def test_get_github_client_no_token(app_inst):
    from app.workspace.routes import get_github_client
    with app_inst.test_request_context():
        assert get_github_client() is None

@patch('app.workspace.routes.Github')
def test_download_repo_no_name(mock_github, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake_token'
    response = client.post('/api/workspace/download', json={})
    assert response.status_code == 400

def test_apply_patch_no_file(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'test'
    response = client.post('/api/workspace/modify/patch', data={})
    assert response.status_code == 400

def test_apply_patch_empty_filename(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'test'
    response = client.post('/api/workspace/modify/patch', data={'file': (io.BytesIO(b""), '')}, content_type='multipart/form-data')
    assert response.status_code == 400

@patch('git.Repo')
def test_apply_patch_git_error(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'
    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)
    mock_repo = MagicMock()
    mock_repo.git.apply.side_effect = Exception("Patch failed")
    mock_repo_class.return_value = mock_repo

    response = client.post('/api/workspace/modify/patch', data={'file': (io.BytesIO(b"diff"), 't.patch')}, content_type='multipart/form-data')
    assert response.status_code == 500

def test_upload_file_no_file(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'test'
    response = client.post('/api/workspace/modify/upload', data={})
    assert response.status_code == 400

def test_upload_archive_no_archive(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'test'
    response = client.post('/api/workspace/modify/archive', data={})
    assert response.status_code == 400

def test_upload_archive_empty_filename(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'test'
    response = client.post('/api/workspace/modify/archive', data={'archive': (io.BytesIO(b""), '')}, content_type='multipart/form-data')
    assert response.status_code == 400

def test_upload_archive_unsupported(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'test'
        sess['session_id'] = 'test_session'
    response = client.post('/api/workspace/modify/archive', data={'archive': (io.BytesIO(b""), 't.txt')}, content_type='multipart/form-data')
    assert response.status_code == 400

@patch('tarfile.open')
def test_upload_archive_tar_slip(mock_tar, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'
    mock_tar_instance = MagicMock()
    mock_member = MagicMock()
    mock_member.name = '../evil.txt'
    mock_tar_instance.getmembers.return_value = [mock_member]
    mock_tar.return_value.__enter__.return_value = mock_tar_instance

    data = {'archive': (io.BytesIO(b""), 'test.tar.gz')}
    response = client.post('/api/workspace/modify/archive', data=data, content_type='multipart/form-data')
    assert response.status_code == 500
    assert "Tar Slip" in response.get_json()['error']

def test_commit_no_message(client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'
    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)
    response = client.post('/api/workspace/commit', json={})
    assert response.status_code == 400

@patch('git.Repo')
def test_commit_error(mock_repo_class, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'
    os.makedirs('/tmp/gh-web-workspaces/test_session/testrepo/.git', exist_ok=True)
    mock_repo = MagicMock()
    mock_repo.git.add.side_effect = Exception("Git add failed")
    mock_repo_class.return_value = mock_repo
    response = client.post('/api/workspace/commit', json={'commit_message': 'msg'})
    assert response.status_code == 500

# Hit Unauthorized lines
def test_prs_unauthorized(client):
    assert client.get('/api/repos/o/r/prs').status_code == 401
    assert client.post('/api/repos/o/r/prs').status_code == 401
    assert client.post('/api/repos/o/r/prs/1/merge').status_code == 401

def test_workspace_unauthorized(client):
    assert client.post('/api/workspace/clone').status_code == 401
    assert client.post('/api/workspace/download').status_code == 401

def test_workspace_no_params(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake'
    assert client.post('/api/workspace/clone', json={}).status_code == 400

@patch('app.workspace.routes.os.path.exists')
def test_workspace_already_cloned(mock_exists, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake'
        sess['session_id'] = 'test_session'

    def side_effect(path):
        if '.git' in path: return True
        return True

    mock_exists.side_effect = side_effect
    response = client.post('/api/workspace/clone', json={'repo_url': 'http://github.com/o/r'})
    assert response.status_code == 200
    assert "already cloned" in response.get_json()['message']

def test_modify_no_active_repo(client):
    assert client.post('/api/workspace/modify/patch').status_code == 400
    assert client.post('/api/workspace/modify/upload').status_code == 400
    assert client.post('/api/workspace/modify/archive').status_code == 400
    assert client.post('/api/workspace/commit').status_code == 400

@patch('app.workspace.routes.git.Repo.clone_from')
def test_clone_error(mock_clone, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake'
        sess['session_id'] = 'test_session'
    mock_clone.side_effect = Exception("Clone failed")
    response = client.post('/api/workspace/clone', json={'repo_url': 'http://github.com/o/r'})
    assert response.status_code == 500

@patch('app.workspace.routes.get_github_client')
def test_download_error(mock_get_client, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake'
        sess['session_id'] = 'test_session'
    mock_get_client.return_value.get_repo.side_effect = Exception("API error")
    response = client.post('/api/workspace/download', json={'repo_name': 'o/r'})
    assert response.status_code == 500

@patch('app.workspace.routes.subprocess.run')
def test_patch_error_downloaded(mock_run, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'
    repo_path = '/tmp/gh-web-workspaces/test_session/testrepo'
    os.makedirs(repo_path, exist_ok=True)
    if os.path.exists(os.path.join(repo_path, '.git')):
        shutil.rmtree(os.path.join(repo_path, '.git'))
    mock_run.side_effect = Exception("patch command failed")
    response = client.post('/api/workspace/modify/patch', data={'file': (io.BytesIO(b"diff"), 't.patch')}, content_type='multipart/form-data')
    assert response.status_code == 500

@patch('zipfile.ZipFile')
def test_upload_archive_zip_success(mock_zip, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'
    mock_zip_instance = MagicMock()
    mock_zip_instance.namelist.return_value = ['safe.txt']
    mock_zip.return_value.__enter__.return_value = mock_zip_instance
    response = client.post('/api/workspace/modify/archive', data={'archive': (io.BytesIO(b""), 't.zip')}, content_type='multipart/form-data')
    assert response.status_code == 200

def test_before_request_session_id(client):
    with client.session_transaction() as sess:
        pass # empty session
    client.get('/')
    with client.session_transaction() as sess:
        assert 'session_id' in sess

@patch('app.prs.routes.get_github_client')
def test_prs_errors(mock_get_client, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake'

    mock_get_client.return_value.get_repo.side_effect = Exception("PR error")
    assert client.get('/api/repos/o/r/prs').status_code == 500
    assert client.post('/api/repos/o/r/prs', json={'title':'t','head':'h','base':'b'}).status_code == 500
    assert client.post('/api/repos/o/r/prs/1/merge', json={}).status_code == 500

@patch('app.prs.routes.get_github_client')
def test_create_pr_missing(mock_get_client, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake'
    assert client.post('/api/repos/o/r/prs', json={}).status_code == 400

@patch('app.prs.routes.get_github_client')
def test_merge_pr_failed_merged(mock_get_client, client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake'
    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_status = MagicMock()
    mock_status.merged = False
    mock_pr.merge.return_value = mock_status
    mock_repo.get_pull.return_value = mock_pr
    mock_get_client.return_value.get_repo.return_value = mock_repo
    assert client.post('/api/repos/o/r/prs/1/merge', json={}).status_code == 400

@patch('tarfile.open')
def test_upload_archive_tar_success(mock_tar, client):
    with client.session_transaction() as sess:
        sess['active_repo'] = 'testrepo'
        sess['session_id'] = 'test_session'
    mock_tar_instance = MagicMock()
    mock_member = MagicMock()
    mock_member.name = 'safe.txt'
    mock_tar_instance.getmembers.return_value = [mock_member]
    mock_tar.return_value.__enter__.return_value = mock_tar_instance
    response = client.post('/api/workspace/modify/archive', data={'archive': (io.BytesIO(b""), 't.tar.gz')}, content_type='multipart/form-data')
    assert response.status_code == 200

def test_is_safe_path_unsafe_symlink(app_inst):
    from app.workspace.routes import is_safe_path
    assert is_safe_path('/tmp', '/etc/passwd') == False

def test_is_safe_path_not_follow_symlinks(app_inst):
    from app.workspace.routes import is_safe_path
    assert is_safe_path('/tmp', '/tmp/foo', follow_symlinks=False) == True
