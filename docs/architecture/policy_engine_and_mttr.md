# Architectural Design: Policy Engine & Remediation Pulse

## 1. Overview
Strategic Governance Phase 3 transforms GH-Web from a monitoring tool into an active guardrail system. This is achieved by introducing a server-side **Policy Engine** that evaluates repository state against defined rules and extending the **Pulse Metrics Engine** to include remediation and debt analytics.

## 2. Policy Engine Architecture

### 2.1. Policy Definition
Policies are defined as JSON objects. For Phase 3, these will be stored in a central server-side configuration, but the engine is designed to support a `.github/gh-web-policy.json` file in the future.

**Example Policy:**
```json
{
  "rules": [
    {
      "id": "no_critical_vulnerabilities",
      "effect": "block_merge",
      "condition": "security.summary.vulnerabilities.critical > 0"
    },
    {
      "id": "ci_must_pass",
      "effect": "block_merge",
      "condition": "health.ci_status != 'success'"
    }
  ]
}
```

### 2.2. Evaluation Logic
A new internal service `GovernanceService` will:
1. Fetch the latest `health` and `security` data for a repository.
2. Evaluate the configured rules using a simple expression evaluator.
3. Return a `policy_status` object:
```json
{
  "compliant": false,
  "violations": ["no_critical_vulnerabilities"],
  "blocked_actions": ["merge_pr", "create_release"]
}
```

## 3. Metrics Engine Extensions (Pulse v2)

### 3.1. Security MTTR (Mean Time to Remediation)
- **Source:** GitHub Dependabot/Security Alerts API (listing 'fixed' alerts).
- **Calculation:**
  - Fetch alerts closed in the last 30 days.
  - MTTR = `average(closed_at - created_at)`.
- **Performance:** This requires a separate API call to fetch closed alerts. To mitigate overhead, this will be calculated only during the full "Pulse" background refresh (60m TTL).

### 3.2. Dependency Freshness Index
- **Source:** Workspace file analysis (`requirements.txt`, `package.json`).
- **Engine:** `FreshnessScanner` will:
  - Parse dependency files.
  - Query a version cache (refreshed daily) to find the delta between the local version and the latest stable.
  - **Formula:** `(Count of dependencies on latest / Total dependencies) * 100`.

## 4. API Extensions

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/repos/<full_name>/governance/policy` | Returns current policy status and violations. |
| `PATCH` | `/api/repos/<full_name>/governance/policy` | Updates repository-specific policy overrides. |
| `GET` | `/api/workspace/dependency-freshness` | Triggers a scan of the active workspace for dependency versions. |

## 5. UI/UX Changes
- **PR Tab:** The "Merge" button will be visually "locked" (disabled with an info icon) if a `block_merge` violation exists.
- **Dashboard:** Repository cards will display a "Policy" status badge (Compliant/Non-Compliant).
- **Pulse Component:** Add "MTTR" and "Freshness" meters to the Portfolio Pulse view.

## 6. Security Considerations
- **Bypass Mechanism:** Admins can be allowed to "Force Merge" if they have sufficient GitHub permissions, but GH-Web will record the policy bypass.
- **Resource Limits:** Version analysis is limited to 100 dependencies per file to prevent DoS via massive manifest files.
