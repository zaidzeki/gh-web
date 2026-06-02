# PRD: Strategic Governance Phase 5 - Interactive Policy Control & Tactical Governance

## 1. Problem Statement
Strategic Governance Phase 4 successfully introduced the Portfolio Heatmap and a persistent `PolicyStore`. However, the current implementation is "Observation-First." Users can see high-risk outliers (Red Zone repos) and SLA violations, but the path to remediation or policy adjustment involves too many steps. There is a "Governance Gap" between identifying an outlier and managing its compliance rules. Furthermore, organizational-level guardrails are not yet exposed to users.

## 2. Objectives
- **Close the Loop:** Make the Portfolio Heatmap interactive, allowing users to jump directly from a data point to governance management.
- **Organizational Guardrails:** Enable authorized users to manage policies at the organization level, providing a top-down approach to compliance.
- **Tactical SLA Enforcement:** Move from "Passive Alerting" to "Active Countdown" by surfacing precise SLA deadlines in the Task Inbox.

## 3. User Stories
- **As a Security Architect,** I want to click on a repository dot in the "Red Zone" of the heatmap to immediately open its governance settings and understand why it's non-compliant.
- **As an Engineering Lead,** I want to set a global "Critical SLA" of 24 hours for my entire organization, rather than configuring every repository manually.
- **As a Developer,** I want to see exactly how much time I have left to patch a critical vulnerability before it triggers a "SLA Violation" and blocks my next PR merge.

## 4. Proposed Features

### 4.1. Interactive Governance Heatmap
- **Actionable Dots:** Clicking a repository dot in the scatter plot opens the "Governance Settings" modal for that specific repository.
- **Contextual Tooltips:** Enhanced tooltips with "Manage Policy" and "Open Workspace" shortcuts.

### 4.2. Organizational Policy Management
- **Org-Level Settings:** A new interface (or modal tab) to manage policies for an entire organization.
- **Hierarchy Awareness:** Visual indicators in the Repo Policy editor showing which rules are inherited from the Organization or Global scope.
- **API:** `GET/PATCH /api/governance/orgs/<org>/policy`.

### 4.3. Tactical SLA Visibility (Task Inbox)
- **Deadline Countdowns:** Security tasks in the Unified Task Inbox will display a countdown (e.g., "SLA: 14h remaining" or "SLA: EXCEEDED").
- **Visual Urgency:** High-priority colors (Orange/Red) for tasks nearing or exceeding their remediation SLA.

### 4.4. Unified Governance Settings Modal
- A comprehensive UI for toggling:
    - `block_merge_on_critical_security`
    - `block_merge_on_failing_ci`
    - `block_merge_on_sla_violation`
    - `sla_critical_hours` (Integer input)

## 5. Acceptance Criteria
- [ ] Portfolio Heatmap dots are clickable and trigger the Governance Modal.
- [ ] Users can view and update policies for an entire organization.
- [ ] Task Inbox displays relative time remaining for Security SLAs.
- [ ] Repository Policy Modal correctly identifies inherited vs. overridden rules.

## 6. Technical Considerations
- **Frontend Interactivity:** The SVG heatmap must support event listeners for individual `<circle>` elements.
- **SLA Calculation:** The backend must calculate `alert_age` relative to `sla_critical_hours` and expose `deadline` as an ISO timestamp.
- **Permission Mapping:** Updating organization-level policies should require "Admin" or "Maintainer" roles on the GitHub organization.
