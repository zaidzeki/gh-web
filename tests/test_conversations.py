import pytest
from unittest.mock import MagicMock, patch
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-key"
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def session_with_token(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'test-token'
        sess['session_id'] = 'test-session'

@patch('app.issues.routes.Github')
def test_get_comments(mock_github, client, session_with_token):
    mock_repo = MagicMock()
    mock_issue = MagicMock()
    mock_comment = MagicMock()

    mock_comment.user.login = "tester"
    mock_comment.user.avatar_url = "http://avatar.url"
    mock_comment.body = "test comment"
    mock_comment.created_at = None

    mock_github.return_value.get_repo.return_value = mock_repo
    mock_repo.get_issue.return_value = mock_issue
    mock_issue.get_comments.return_value = [mock_comment]

    response = client.get('/api/repos/owner/repo/issues/1/comments')

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['user'] == "tester"
    assert data[0]['body'] == "test comment"

@patch('app.issues.routes.Github')
def test_post_comment(mock_github, client, session_with_token):
    mock_repo = MagicMock()
    mock_issue = MagicMock()
    mock_comment = MagicMock()

    mock_comment.user.login = "tester"
    mock_comment.created_at = None

    mock_github.return_value.get_repo.return_value = mock_repo
    mock_repo.get_issue.return_value = mock_issue
    mock_issue.create_comment.return_value = mock_comment

    response = client.post('/api/repos/owner/repo/issues/1/comments',
                           json={"body": "new comment"})

    assert response.status_code == 201
    assert response.get_json()['message'] == "Comment posted successfully"
    mock_issue.create_comment.assert_called_once_with("new comment")

@patch('app.prs.routes.Github')
def test_submit_review(mock_github, client, session_with_token):
    mock_repo = MagicMock()
    mock_pr = MagicMock()

    mock_github.return_value.get_repo.return_value = mock_repo
    mock_repo.get_pull.return_value = mock_pr

    response = client.post('/api/repos/owner/repo/prs/1/reviews',
                           json={"body": "looks good", "event": "APPROVE"})

    assert response.status_code == 200
    assert response.get_json()['message'] == "Review APPROVE submitted successfully"
    mock_pr.create_review.assert_called_once_with(body="looks good", event="APPROVE")
