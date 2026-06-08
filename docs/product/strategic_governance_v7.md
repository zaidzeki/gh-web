# PRD: Strategic Governance Phase 7 - Mission Control & Contextual Health

## 1. Problem Statement
The current GH-Web dashboard suffers from a **"Workspace Lock."** Strategic oversight widgets (Portfolio Pulse, Heatmap, Roadmap) only display data for repositories that are currently active in a server-side workspace (cloned/downloaded).

While logical for developers, this represents a significant barrier for **Product Leads and Engineering Managers** who need high-level oversight across an entire Organization or Team without the overhead of "cloning" every microservice. Strategic insight should be driven by **context** (Current Org/Team), not just local filesystem state.

## 2. Objectives
- **Decouple Insight from Workspaces:** Transition the dashboard widgets to use the current user context (Organization/Team) as the primary data source.
- **Unified Mission Control:** Transform the Dashboard into a true "Mission Control" center where health is visible for all repositories in the selected scope.
- **Persona-Driven Visibility:** Enable non-developer personas to monitor DORA metrics and Security MTTR across the entire org without interacting with the Workspace engine.

## 3. User Stories
- **As an Engineering Manager,** I want to see the Pulse (DORA) metrics for all repositories in my Organization, regardless of whether I have cloned them locally.
- **As a Product Lead,** I want the Portfolio Roadmap to show milestones for the entire Team context so I can track cross-project goals.
- **As a Security Lead,** I want the Governance Heatmap to visualize risk across the whole portfolio so I can identify outliers that need attention.

## 4. Proposed Features

### 4.1. Context-Aware Portfolio Aggregation
- Update the backend aggregation endpoints (`/api/workspace/portfolio/*`) to accept optional `org_name` and `team_id` parameters.
- If no repositories are active in the workspace, default to the top 20 most recently pushed repositories in the current context.

### 4.2. Mission Control Dashboard
- Rename the dashboard sections to reflect their broader scope (e.g., "Context Pulse" instead of "Portfolio Pulse").
- Add a "Scope" indicator to the widgets (e.g., "Viewing: Org 'Acme-Corp'").

### 4.3. "Ghost" Workspace Support
- Surface "Not Cloned" indicators in the Pulse view for repositories that are being monitored via API but don't have a local workspace.
- Provide a one-click "Initialize Workspace" action from any widget outlier (e.g., click a red dot on the heatmap to clone).

## 5. Acceptance Criteria
- [ ] Portfolio Pulse displays aggregated DORA metrics for the current Org/Team context when no workspaces are active.
- [ ] Portfolio Roadmap displays milestones for all repositories in the current scope.
- [ ] Governance Heatmap maps coordinates for all repositories in the selected Organization.
- [ ] UI widgets update dynamically when the Context Switcher (Org/Team) is changed.

## 6. Technical Considerations
- **API Optimization:** Parallel fetching (ThreadPoolExecutor) is mandatory to handle Org-level aggregation (capped at 20 repos for performance).
- **Freshness Fallback:** Dependency Freshness logic must handle "Workspace Missing" states gracefully (returning 'N/A' or a 'Requires Clone' status).
- **Caching:** Aggressive server-side caching (60m TTL) for Org-level metrics to prevent hitting GitHub rate limits.
