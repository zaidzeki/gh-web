# PRD: Operational Health Phase 2 - Proactive Governance & Filtering

## 1. Problem Statement
The current implementation of Operational Health provides visibility but lacks **actionability**. Users can see badges, but they cannot easily filter for "blocked" repositories (those with failing CI) or see the health of their active workspaces in the portfolio view. In a large portfolio, scrolling to find a failing repository is inefficient.

## 2. Objectives
- **Drive Focused Governance:** Allow users to instantly filter the dashboard to show only repositories requiring attention (Failing CI, Modified but uncommitted).
- **Enrich Workspace Portfolio:** Surface CI health for all active workspaces directly in the portfolio view to prevent "hidden" failures in background clones.
- **Contextual Health Visibility:** Display the CI status of the active branch/PR in the Workspace tab header.

## 3. User Stories
- **As a Tech Lead,** I want to filter my dashboard for "Failing" repositories so I can prioritize helping my team fix broken builds.
- **As a Developer,** I want to see the CI status of all my active workspaces in one place so I don't forget about a failing build in a background task.
- **As a Contributor,** I want to see the live CI status of my active task in the Workspace header so I know when it's safe to submit my PR.

## 4. Proposed Features

### 4.1. Dashboard Health Filtering
- **Filter Pills/Dropdown:** UI elements on the Dashboard to filter repositories by:
    - **All:** Default view.
    - **Failing:** Repositories where the latest CI status is `failure`.
    - **Pending:** Repositories with active CI runs.
    - **Modified:** Repositories with local workspace changes (sync with Portfolio).

### 4.2. Portfolio Health Enrichment
- **CI Badges in Portfolio:** The `workspace_portfolio` view on the Dashboard will display CI status badges for the current HEAD of each local clone.

### 4.3. Workspace Header CI Indicator
- **Live Status:** The Workspace tab header will display a color-coded badge for the CI status of the active branch/PR.

## 5. Acceptance Criteria
- [ ] Dashboard Repo List supports filtering by health status (client-side implementation).
- [ ] `GET /api/workspace/portfolio` returns `ci_status` for each workspace.
- [ ] Portfolio cards on the Dashboard display CI status badges.
- [ ] Workspace header displays CI status for the active repository.

## 6. Technical Considerations
- **Filtering Logic:** Since health data is lazy-loaded, the filter must handle repositories whose health hasn't been fetched yet (likely by triggering a fetch if not present).
- **API Performance:** `workspace_portfolio` will now involve N+1 GitHub API calls if we fetch CI status for each. This should be optimized or accepted given the typically small number of active workspaces (portfolio is capped by active clones).
