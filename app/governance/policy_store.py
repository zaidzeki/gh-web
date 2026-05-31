import os
import json
import threading

class PolicyStore:
    def __init__(self, storage_path='app/data/policies.json'):
        self.storage_path = storage_path
        self.lock = threading.Lock()
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            default_data = {
                "scopes": {
                    "global": {
                        "block_merge_on_critical_security": True,
                        "block_merge_on_failing_ci": True,
                        "sla_critical_hours": 48,
                        "block_merge_on_sla_violation": True
                    },
                    "orgs": {},
                    "repos": {}
                }
            }
            self._save(default_data)

    def _load(self):
        with self.lock:
            try:
                if not os.path.exists(self.storage_path):
                    return {"scopes": {"global": {}, "orgs": {}, "repos": {}}}
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {"scopes": {"global": {}, "orgs": {}, "repos": {}}}

    def _save(self, data):
        with self.lock:
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

    def get_effective_policy(self, repo_full_name):
        """
        Resolves policy using hierarchy: Repo -> Org -> Global.
        """
        data = self._load()
        scopes = data.get("scopes", {})

        # 1. Global defaults
        policy = scopes.get("global", {}).copy()

        # 2. Org overrides
        org_name = repo_full_name.split('/')[0] if '/' in repo_full_name else None
        if org_name and org_name in scopes.get("orgs", {}):
            policy.update(scopes["orgs"][org_name])

        # 3. Repo overrides
        if repo_full_name in scopes.get("repos", {}):
            policy.update(scopes["repos"][repo_full_name])

        return policy

    def update_repo_policy(self, repo_full_name, updates):
        data = self._load()
        if "repos" not in data["scopes"]:
            data["scopes"]["repos"] = {}

        if repo_full_name not in data["scopes"]["repos"]:
            data["scopes"]["repos"][repo_full_name] = {}

        data["scopes"]["repos"][repo_full_name].update(updates)
        self._save(data)
        return data["scopes"]["repos"][repo_full_name]

    def get_raw_data(self):
        return self._load()
