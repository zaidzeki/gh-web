import pytest
from app import create_app
from unittest.mock import patch

@pytest.mark.parametrize("pkg,ver,expected", [
    ('flask', '2.0.1\nmalicious==1.0', 400),
    ('requests[security]', '2.25.1+build1', 200)
])
def test_remediate_batch_validation(pkg, ver, expected):
    app = create_app({'TESTING': True})
    with app.test_request_context('/api/governance/remediate/batch', method='POST',
                                  json={'package': pkg, 'fixed_version': ver, 'repos': ['owner/repo']}):
        with patch('app.governance.routes.session', {'github_token': 'fake_token'}), \
             patch('app.governance.routes.Github'), \
             patch('app.governance.routes.ThreadPoolExecutor') as mock_ex:
            mock_ex.return_value.__enter__.return_value.submit.return_value.result.return_value = ("r", "success", "url")
            from app.governance.routes import remediate_batch
            _, status_code = remediate_batch()
            assert status_code == expected
