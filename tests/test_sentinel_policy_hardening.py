import os
import json
import threading
import time
import pytest
import stat
from app.governance.policy_store import PolicyStore

@pytest.fixture
def temp_policy_store(tmp_path):
    policy_file = tmp_path / "policies.json"
    return PolicyStore(storage_path=str(policy_file))

def test_strict_file_permissions(temp_policy_store):
    path = temp_policy_store.storage_path
    mode = os.stat(path).st_mode
    # Owner-only read/write is 0o600
    assert (mode & 0o077) == 0, f"Permissions are too loose: {oct(mode)}"

def test_no_mass_assignment(temp_policy_store):
    org_name = "test-org"
    updates = {"malicious_key": "injected_value", "block_merge_on_critical_security": False}

    temp_policy_store.update_org_policy(org_name, updates)

    policy = temp_policy_store.get_org_policy(org_name)
    assert "malicious_key" not in policy, "Arbitrary keys should be blocked"
    assert policy["block_merge_on_critical_security"] is False

def test_atomic_update_no_race(temp_policy_store, mocker):
    org_name = "atomic-race-org"

    # Use allowed keys for race test
    # Initial state is True/True

    # Mock _load to introduce a delay after loading
    original_load = temp_policy_store._load
    def delayed_load():
        data = original_load()
        time.sleep(0.1)
        return data

    mocker.patch.object(temp_policy_store, '_load', side_effect=delayed_load)

    def update_worker(key, value):
        temp_policy_store.update_org_policy(org_name, {key: value})

    # Thread 1 sets one policy to False
    t1 = threading.Thread(target=update_worker, args=("block_merge_on_critical_security", False))
    # Thread 2 sets another policy to False
    t2 = threading.Thread(target=update_worker, args=("block_merge_on_failing_ci", False))

    t1.start()
    time.sleep(0.05)
    t2.start()

    t1.join()
    t2.join()

    policy = temp_policy_store.get_org_policy(org_name)
    # Both should be False if updates are atomic and no data is lost
    assert policy["block_merge_on_critical_security"] is False, "First update lost in race"
    assert policy["block_merge_on_failing_ci"] is False, "Second update lost in race"
