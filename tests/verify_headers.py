import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    return app.test_client()

def test_security_headers(client):
    response = client.get('/')
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    assert 'Content-Security-Policy' in response.headers
    print("\nSecurity headers verified successfully!")

if __name__ == "__main__":
    pytest.main([__file__])
