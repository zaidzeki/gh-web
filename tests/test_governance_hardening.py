import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def test_org_governance_length_limit(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    long_org = "a" * 101
    # GET org policy
    response = client.get(f'/api/governance/orgs/{long_org}/policy')
    assert response.status_code == 400
    assert "org_name is too long" in response.get_json()['error']

    # PATCH org policy
    response = client.patch(f'/api/governance/orgs/{long_org}/policy', json={})
    assert response.status_code == 400
    assert "org_name is too long" in response.get_json()['error']

def test_portfolio_heatmap_repo_length_limit(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    long_repo = "a" * 256
    response = client.get(f'/api/workspace/portfolio/governance/heatmap?repos={long_repo}')
    assert response.status_code == 400
    assert "Repository name too long" in response.get_json()['error']

def test_remediate_batch_length_limits(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    # Test package name limit
    long_package = "a" * 101
    response = client.post('/api/governance/remediate/batch', json={
        "package": long_package,
        "fixed_version": "1.0.0",
        "repos": ["owner/repo"]
    })
    assert response.status_code == 400
    assert "package name is too long" in response.get_json()['error']

    # Test fixed_version limit
    long_version = "a" * 101
    response = client.post('/api/governance/remediate/batch', json={
        "package": "flask",
        "fixed_version": long_version,
        "repos": ["owner/repo"]
    })
    assert response.status_code == 400
    assert "fixed_version is too long" in response.get_json()['error']

    # Test repo name limit in batch
    long_repo = "a" * 256
    response = client.post('/api/governance/remediate/batch', json={
        "package": "flask",
        "fixed_version": "1.0.0",
        "repos": [long_repo]
    })
    assert response.status_code == 400
    assert "Repository name too long" in response.get_json()['error']

def test_remediation_suggestions_repo_length_limit(client):
    with client.session_transaction() as sess:
        sess['github_token'] = 'fake-token'

    long_repo = "a" * 256
    response = client.get(f'/api/governance/remediate/suggestions?repos={long_repo}')
    assert response.status_code == 400
    assert "Repository name too long" in response.get_json()['error']
