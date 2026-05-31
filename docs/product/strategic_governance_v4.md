# PRD: Strategic Governance Phase 4 - Dynamic Policies & Governance Heatmap

## 1. Problem Statement
Strategic Governance Phase 3 introduced hard guardrails and new metrics (MTTR, Freshness). However, policies are currently static (defined in code) and the visualization of organizational debt is fragmented across repository cards. Stakeholders lack a "Single Pane of Glass" to identify which teams are accumulating the most technical and security debt relative to their delivery velocity.

## 2. Objectives
- **Dynamic Policy Management:** Allow authorized users to override or customize governance rules per repository or organization.
- **Compliance SLAs:** Introduce time-based SLAs for vulnerability remediation (e.g., Critical alerts must be fixed within 48 hours).
- **Portfolio Governance Heatmap:** Provide a high-density visualization of the entire portfolio to identify high-risk "Outliers".

## 3. User Stories
- **As a DevOps Manager,** I want to adjust the "Block Merge" policy for a specific legacy repository that cannot meet CI standards, so that we can still perform emergency patches.
- **As a Security Lead,** I want to see a Heatmap of all repositories so I can immediately spot projects with both low dependency freshness and high security MTTR.
- **As a Compliance Officer,** I want repositories to be marked as "Non-Compliant" if they exceed the 48-hour SLA for critical vulnerabilities, regardless of whether they are "Elite" in DORA metrics.

## 4. Proposed Features

### 4.1. Dynamic Policy Overrides
- Implement a persistent `PolicyStore` that allows CRUD operations on governance rules.
- Support rule scoping: Global -> Organization -> Repository.
- UI: A "Governance Settings" modal for repository and organization views.

### 4.2. Portfolio Governance Heatmap
- A new dashboard component that plots every repository in the portfolio on a 2D grid.
- **X-Axis:** Dependency Freshness (0% to 100%).
- **Y-Axis:** Security MTTR (Hours).
- **Quadrant Logic:**
    - **Quadrant 1 (Top Right): "The Vanguard"** - High Freshness, Low MTTR. (Compliant & Modern).
    - **Quadrant 2 (Top Left): "The Artisans"** - Low Freshness, Low MTTR. (Reactive but running on legacy debt).
    - **Quadrant 3 (Bottom Left): "The Red Zone"** - Low Freshness, High MTTR. (Critical Risk: Outdated and slow to fix).
    - **Quadrant 4 (Bottom Right): "The Fragile Elite"** - High Freshness, High MTTR. (Modern but slow to fix new threats).

### 4.3. Compliance SLAs
- Track `alert_created_at` vs `current_time` for open alerts.
- New Metric: `SLA_Compliance_Score`.
- Policy Rule: `block_merge_on_sla_violation`.

## 5. Acceptance Criteria
- [ ] Backend supports `PATCH /api/repos/<full_name>/governance/policy` for dynamic overrides.
- [ ] `GET /api/workspace/portfolio/governance/summary` returns aggregated data for the Heatmap.
- [ ] UI component "Governance Heatmap" correctly categorizes repos into the 4 quadrants.
- [ ] Repositories exceeding SLA (48h for Critical) display a "SLA Violated" warning.

## 6. Technical Considerations
- **Persistence:** Initial implementation using a server-side JSON store (`data/policies.json`), transitioning to database or `.github` file storage.
- **Visualization:** The Heatmap requires a lightweight charting library or a custom SVG/CSS grid implementation to handle 50+ repositories.
