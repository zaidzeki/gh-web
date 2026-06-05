import os
import json
import threading

class PolicyStore:
    ALLOWED_POLICY_KEYS = {
        "block_merge_on_critical_security",
        "block_merge_on_failing_ci",
        "sla_critical_hours",
        "block_merge_on_sla_violation"
    }

    # Security: Hardcoded defaults ensure that even if the persistence layer is corrupted
    # or missing, the application defaults to a secure (fail-closed) state.
    GLOBAL_DEFAULTS = {
        "block_merge_on_critical_security": True,
        "block_merge_on_failing_ci": True,
        "sla_critical_hours": 48,
        "block_merge_on_sla_violation": True
    }

    def __init__(self, storage_path='app/data/policies.json'):
        self.storage_path = storage_path
        # Use RLock to allow nested locking if needed and safer multi-threaded access
        self.lock = threading.RLock()
        self._ensure_storage()

    def _ensure_storage(self):
        with self.lock:
            if not os.path.exists(self.storage_path):
                # Ensure directory exists with restricted permissions (0700)
                os.makedirs(os.path.dirname(self.storage_path), mode=0o700, exist_ok=True)
                try:
                    os.chmod(os.path.dirname(self.storage_path), 0o700)
                except OSError:
                    pass

                default_data = {
                    "scopes": {
                        "global": self.GLOBAL_DEFAULTS.copy(),
                        "orgs": {},
                        "repos": {}
                    }
                }
                self._save(default_data)

    def _load(self):
        """Loads data from storage. Returns empty structure if missing or corrupted."""
        with self.lock:
            try:
                if not os.path.exists(self.storage_path):
                    return {"scopes": {"global": {}, "orgs": {}, "repos": {}}}
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {"scopes": {"global": {}, "orgs": {}, "repos": {}}}

    def _save(self, data):
        """Atomic write to persistence layer with restricted permissions."""
        with self.lock:
            temp_path = self.storage_path + ".tmp"
            try:
                with open(temp_path, 'w') as f:
                    json.dump(data, f, indent=2)

                # Ensure restricted permissions (0600) before moving into place
                os.chmod(temp_path, 0o600)
                # Atomic swap
                os.replace(temp_path, self.storage_path)
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise

    def get_effective_policy(self, repo_full_name):
        """
        Resolves policy using hierarchy: Repo -> Org -> Global.
        """
        policy, _ = self.get_effective_policy_with_sources(repo_full_name)
        return policy

    def get_effective_policy_with_sources(self, repo_full_name):
        """
        Resolves policy using hierarchy: Repo -> Org -> Global.
        Returns (policy, sources)
        """
        with self.lock:
            data = self._load()
            scopes = data.get("scopes", {})

            # 1. Global defaults (hardcoded fallback + persistence overrides)
            policy = self.GLOBAL_DEFAULTS.copy()
            sources = {k: "global" for k in policy.keys()}

            persisted_global = scopes.get("global", {})
            for k, v in persisted_global.items():
                if k in self.ALLOWED_POLICY_KEYS:
                    policy[k] = v

            # 2. Org overrides
            org_name = repo_full_name.split('/')[0] if '/' in repo_full_name else None
            if org_name and org_name in scopes.get("orgs", {}):
                org_policy = scopes["orgs"][org_name]
                for k, v in org_policy.items():
                    policy[k] = v
                    sources[k] = "org"

            # 3. Repo overrides
            if repo_full_name in scopes.get("repos", {}):
                repo_policy = scopes["repos"][repo_full_name]
                for k, v in repo_policy.items():
                    policy[k] = v
                    sources[k] = "repo"

            return policy, sources

    def get_org_policy(self, org_name):
        """
        Resolves policy for an organization: Org overrides + Global defaults.
        """
        policy, _ = self.get_org_policy_with_sources(org_name)
        return policy

    def get_org_policy_with_sources(self, org_name):
        """
        Resolves policy for an organization: Org overrides + Global defaults.
        Returns (policy, sources)
        """
        with self.lock:
            data = self._load()
            scopes = data.get("scopes", {})

            # Start with hardcoded defaults, overlay persisted global overrides
            policy = self.GLOBAL_DEFAULTS.copy()
            sources = {k: "global" for k in policy.keys()}

            persisted_global = scopes.get("global", {})
            for k, v in persisted_global.items():
                if k in self.ALLOWED_POLICY_KEYS:
                    policy[k] = v

            if org_name in scopes.get("orgs", {}):
                org_policy = scopes["orgs"][org_name]
                for k, v in org_policy.items():
                    policy[k] = v
                    sources[k] = "org"

            return policy, sources

    def _validate_updates(self, updates):
        """Validates that policy updates have correct types and values."""
        for k, v in updates.items():
            if k in ["block_merge_on_critical_security", "block_merge_on_failing_ci", "block_merge_on_sla_violation"]:
                if not isinstance(v, bool):
                    raise ValueError(f"Value for {k} must be a boolean")
            elif k == "sla_critical_hours":
                if type(v) is not int or v <= 0:
                    raise ValueError(f"Value for {k} must be a positive integer")

    def update_org_policy(self, org_name, updates):
        with self.lock:
            data = self._load()
            if "orgs" not in data["scopes"]:
                data["scopes"]["orgs"] = {}

            if org_name not in data["scopes"]["orgs"]:
                data["scopes"]["orgs"][org_name] = {}

            # Security: Whitelist keys to prevent mass assignment
            filtered_updates = {k: v for k, v in updates.items() if k in self.ALLOWED_POLICY_KEYS}
            self._validate_updates(filtered_updates)

            data["scopes"]["orgs"][org_name].update(filtered_updates)
            self._save(data)
            return data["scopes"]["orgs"][org_name]

    def update_repo_policy(self, repo_full_name, updates):
        with self.lock:
            data = self._load()
            if "repos" not in data["scopes"]:
                data["scopes"]["repos"] = {}

            if repo_full_name not in data["scopes"]["repos"]:
                data["scopes"]["repos"][repo_full_name] = {}

            # Security: Whitelist keys to prevent mass assignment
            filtered_updates = {k: v for k, v in updates.items() if k in self.ALLOWED_POLICY_KEYS}
            self._validate_updates(filtered_updates)

            data["scopes"]["repos"][repo_full_name].update(filtered_updates)
            self._save(data)
            return data["scopes"]["repos"][repo_full_name]

    def get_raw_data(self):
        with self.lock:
            return self._load()
