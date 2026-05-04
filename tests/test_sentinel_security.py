
import pytest
from app.workspace.utils import mask_token

def test_mask_token_types():
    # Test session token masking (handled via session in real request, but here we test regex)
    # Note: mask_token uses session.get('github_token') if in request context.
    # We are testing the regex fallback.

    # Classic Personal Access Token (ghp_) - 40 chars total: ghp_ + 36 chars
    token_36 = "1234567890abcdefghijklmnopqrstuvwxyz"
    assert mask_token(f"ghp_{token_36}") == "********"

    # OAuth Access Token (gho_)
    assert mask_token(f"gho_{token_36}") == "********"

    # User-to-Server Token (ghu_)
    assert mask_token(f"ghu_{token_36}") == "********"

    # Installation Access Token (ghs_)
    assert mask_token(f"ghs_{token_36}") == "********"

    # Runner Registration/Removal Token (ghr_)
    assert mask_token(f"ghr_{token_36}") == "********"

    # Fine-grained Personal Access Token (github_pat_)
    # github_pat_ (11) + 22 chars + _ + 59 chars = 93 chars total
    p1 = "1234567890abcdefghijkl" # 22
    p2 = "12345678901234567890123456789012345678901234567890123456789" # 59
    pat = f"github_pat_{p1}_{p2}"
    assert mask_token(pat) == "********"

def test_mask_token_in_string():
    token_36 = "1234567890abcdefghijklmnopqrstuvwxyz"
    error_msg = f"fatal: Authentication failed for 'https://ghp_{token_36}@github.com/user/repo.git/'"
    expected = "fatal: Authentication failed for 'https://********@github.com/user/repo.git/'"
    assert mask_token(error_msg) == expected

    error_msg_gho = f"Error using token gho_{token_36} with API"
    expected_gho = "Error using token ******** with API"
    assert mask_token(error_msg_gho) == expected_gho

def test_mask_token_no_leak():
    safe_string = "This is a safe string without any tokens."
    assert mask_token(safe_string) == safe_string

    # Too short to be a token
    short_token = "ghp_123"
    assert mask_token(short_token) == short_token
