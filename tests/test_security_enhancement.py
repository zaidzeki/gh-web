import os
import stat
import pytest
from app.workspace.utils import mask_token, get_templates_root
from unittest.mock import patch

def test_mask_token_all_prefixes():
    # Test classic tokens
    assert mask_token("ghp_123456789012345678901234567890123456") == "********"
    assert mask_token("gho_123456789012345678901234567890123456") == "********"
    assert mask_token("ghu_123456789012345678901234567890123456") == "********"
    assert mask_token("ghs_123456789012345678901234567890123456") == "********"
    assert mask_token("ghr_123456789012345678901234567890123456") == "********"

    # Test fine-grained PAT
    fine_grained = "github_pat_1234567890123456789012_12345678901234567890123456789012345678901234567890123456789"
    assert mask_token(fine_grained) == "********"

    # Test mixed content
    mixed = "Error: fatal: Auth failed for https://ghp_123456789012345678901234567890123456@github.com"
    assert "ghp_" not in mask_token(mixed)
    assert "********" in mask_token(mixed)

def test_get_templates_root_permissions(tmp_path):
    # Mock os.path.expanduser to point to our tmp_path
    with patch('os.path.expanduser', return_value=str(tmp_path / ".zekiprod")):
        templates_root = get_templates_root()

        app_root = tmp_path / ".zekiprod"
        assert os.path.exists(app_root)
        assert os.path.exists(templates_root)

        # Check permissions (0700)
        app_root_stat = os.stat(app_root)
        assert stat.S_IMODE(app_root_stat.st_mode) == 0o700

        templates_root_stat = os.stat(templates_root)
        assert stat.S_IMODE(templates_root_stat.st_mode) == 0o700
