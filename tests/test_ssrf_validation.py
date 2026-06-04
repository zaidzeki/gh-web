import pytest
from app.workspace.utils import validate_github_url

def test_validate_github_url():
    # Legitimate URLs
    assert validate_github_url("https://github.com/owner/repo") is True
    assert validate_github_url("http://github.com/owner/repo") is True
    assert validate_github_url("https://www.github.com/owner/repo") is True
    assert validate_github_url("https://github.com/owner/repo.git") is True

    # Malicious URLs (SSRF bypass attempts)
    assert validate_github_url("https://github.com.evil.com/owner/repo") is False
    assert validate_github_url("https://github.com@evil.com/owner/repo") is False
    assert validate_github_url("https://evil.com/github.com/owner/repo") is False
    assert validate_github_url("file:///etc/passwd") is False
    assert validate_github_url("https://127.0.0.1") is False

    # Path traversal in URL
    assert validate_github_url("https://github.com/../evil.com/owner/repo") is False
    assert validate_github_url("https://github.com/owner/repo/../../etc/passwd") is False
    assert validate_github_url("https://github.com/..") is False
    assert validate_github_url("https://github.com/foo/..") is False

    # Edge cases
    assert validate_github_url("") is False
    assert validate_github_url(None) is False
    assert validate_github_url(123) is False
