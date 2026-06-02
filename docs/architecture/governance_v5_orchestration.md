# Architectural Design: Governance Phase 5 - Interactive Orchestration

## 1. Overview
Governance Phase 5 focuses on making the governance engine interactive and extending control to the organizational level. It bridges the gap between the "Portfolio Heatmap" and the "PolicyStore" through a unified orchestration UI.

## 2. API Extensions

### 2.1. Organizational Policy Management
Extending `app/governance/routes.py` to handle organization-scoped policies.

- **GET `/api/governance/orgs/<org>/policy`**
    - Returns the effective policy for the organization (Org overrides + Global defaults).
- **PATCH `/api/governance/orgs/<org>/policy`**
    - Updates overrides in the `scopes.orgs` section of `policies.json`.
    - Payload: `{ "sla_critical_hours": 24, "block_merge_on_failing_ci": true }`

### 2.2. Tactical SLA Metadata
The `Task normalization` logic in `app/tasks/routes.py` will be enriched.

- **Payload Enhancement:**
```json
{
  "id": "owner/repo#123",
  "sla_status": "warning | critical | exceeded",
  "sla_deadline": "2026-06-03T12:00:00Z",
  "sla_remaining_hours": 14
}
```
- **Calculation Logic:**
    1. Resolve `sla_critical_hours` for the repo.
    2. `deadline = alert.created_at + sla_critical_hours`.
    3. `remaining = deadline - now`.

## 3. Frontend Orchestration

### 3.1. Interactive Heatmap (SVG)
- The `renderHeatmap` function in `app.js` will add `onclick` handlers to the SVG `<circle>` elements.
- Interaction: Clicking a circle calls `openGovernanceManager(repo_full_name)`.

### 3.2. Governance Manager Modal
A new multi-tab or contextual modal in `index.html`:
- **Repository Tab:** Manages overrides for the active repository.
- **Organization Tab:** Manages overrides for the parent organization (if user has permissions).
- **Audit View:** Shows the resolution path (e.g., "Inherited from Global" vs "Overridden locally").

### 3.3. Task Inbox SLA Countdown
- The `refreshTaskInbox` function will render a countdown timer or "Time Left" badge for tasks of category `security_vulnerability`.
- CSS classes will map `sla_status` to colors (e.g., `.text-warning`, `.text-danger`).

## 4. Policy Inheritance Visualization
To ensure clarity for administrators, the Policy UI will perform a "Dry Run" resolution:
1. Fetch Global Policy.
2. Fetch Org Overrides.
3. Fetch Repo Overrides.
4. Compare values to identify the source of each effective rule.

## 5. Security & Permissions
- **Org Policy Updates:** Backend will verify that the authenticated user has `admin:org` or `write:org` permissions before allowing `PATCH` operations on organizational scopes.
- **Repo Policy Updates:** Maintain current requirement for `push` access on the repository.
