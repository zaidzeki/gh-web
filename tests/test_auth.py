import pytest
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

def test_login_success(client):
    response = client.post('/login', data={'token': 'test_token'})
    assert response.status_code == 200
    assert response.get_json() == {"message": "Logged in successfully"}
    with client.session_transaction() as sess:
        assert sess['github_token'] == 'test_token'

def test_login_no_token(client):
    response = client.post('/login', data={})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Token is required"}
