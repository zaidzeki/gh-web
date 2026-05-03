
import pytest
from app.workspace.utils import mask_token

def test_mask_all_classic_tokens():
    tokens = [
        "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        "gho_1234567890abcdefghijklmnopqrstuvwxyz",
        "ghu_1234567890abcdefghijklmnopqrstuvwxyz",
        "ghs_1234567890abcdefghijklmnopqrstuvwxyz",
        "ghr_1234567890abcdefghijklmnopqrstuvwxyz"
    ]

    for token in tokens:
        input_str = f"Error: authentication failed for {token}"
        masked = mask_token(input_str)
        assert token not in masked
        assert "********" in masked

def test_mask_fine_grained_token():
    token = "github_pat_1234567890123456789012_12345678901234567890123456789012345678901234567890123456789"
    input_str = f"Token {token} is invalid"
    masked = mask_token(input_str)
    assert token not in masked
    assert "********" in masked
