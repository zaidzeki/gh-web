import os
import json
import pytest
from app.governance.policy_store import PolicyStore
from app.governance.routes import evaluate_repo_policy
from unittest.mock import MagicMock

@pytest.fixture
def temp_policy_store(tmp_path):
    policy_file = tmp_path / "policies.json"
    return PolicyStore(storage_path=str(policy_file))

def test_boolean_policy_validation(temp_policy_store):
    org_name = "bypass-org"
    updates = {"block_merge_on_critical_security": "not-a-boolean"}

    with pytest.raises(ValueError, match="Value for block_merge_on_critical_security must be a boolean"):
        temp_policy_store.update_org_policy(org_name, updates)

def test_sla_hours_validation(temp_policy_store):
    org_name = "invalid-sla-org"

    # Negative hours
    with pytest.raises(ValueError, match="Value for sla_critical_hours must be a positive integer"):
        temp_policy_store.update_org_policy(org_name, {"sla_critical_hours": -10})

    # Non-integer
    with pytest.raises(ValueError, match="Value for sla_critical_hours must be a positive integer"):
        temp_policy_store.update_org_policy(org_name, {"sla_critical_hours": "twenty-four"})

def test_evaluate_repo_policy_type_safety(temp_policy_store, mocker):
    # This test verifies that we can no longer put invalid types in the store
    # and thus evaluate_repo_policy is safer.
    full_name = "test/repo"

    with pytest.raises(ValueError):
        temp_policy_store.update_repo_policy(full_name, {"sla_critical_hours": "invalid"})
