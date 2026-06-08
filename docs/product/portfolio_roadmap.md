# 🌅 Horizon: Portfolio Goal Governance & Unified Roadmap

## 💡 The Pivot
GH-Web has evolved from a single-repo management tool into a multi-workspace cockpit. However, even with "Next Milestone" visibility on the dashboard, users lack a high-level view of how their efforts across *multiple* repositories align with broader timelines. We are pivoting to **Portfolio Goal Governance**. By aggregating milestones across the entire active portfolio, we provide a unified roadmap that helps maintainers balance workload and prioritize "Fixes" based on strategic deadlines.

## ♻️ The Leverage
- **Milestone API:** Reuses the existing `milestones` blueprint and repository discovery logic.
- **Health Monitoring:** Extends the parallel fetching pattern used in `GET /api/repos/health`.
- **Portfolio Engine:** Integrates with the `workspace_portfolio` and the new **Contextual Mission Control** engine.
- **UI Components:** Reuses the card-based layout and progress bars from the repository-specific milestones tab.

## 🚀 The Delta
- **Backend:**
    - `GET /api/workspace/portfolio/milestones`: A context-aware endpoint that aggregates "open" milestones for all repositories in the current Organization/Team scope.
    - Enrichment of milestone data with `repo_name` and `context_relevance`.
- **Frontend:**
    - **Mission Control Roadmap View:** A new section on the Dashboard (or a dedicated modal) that displays milestones across the entire selected context (Org/Team).
    - **Deadline Sort:** Automatic sorting of milestones by `due_on` across different repositories.
    - **Goal-Driven Context Switching:** Clicking a milestone in the roadmap automatically activates that repository and filters the Task Inbox.

## 🎯 The Impact
- **Cross-Project Coordination:** Users can see at a glance if two major releases are landing in the same week across different repositories.
- **Strategic Prioritization:** Shifts focus from "clearing the inbox" to "hitting the goals."
- **Enterprise Readiness:** Provides the "Executive View" necessary for managing complex organizational portfolios.

## 🛠 User Stories
- **As a Lead Maintainer**, I want to see a unified timeline of milestones for all my active workspaces, so that I can identify scheduling conflicts.
- **As a Developer**, I want to see which milestone is most urgent across all my projects, so that I know where my "Fix" efforts are most needed.
- **As a Product Owner**, I want to track the overall progress of a feature spanning multiple repositories (e.g., frontend and backend repos) in one view.

## ✅ Acceptance Criteria
- [x] Users can view an aggregated list of open milestones from all repositories in their active portfolio.
- [x] Milestones are sorted by due date across the entire portfolio.
- [x] Each milestone card indicates which repository it belongs to.
- [x] The view handles repositories with no milestones gracefully (empty state).
- [x] Performance remains snappy (fetching milestones in parallel for up to 50 portfolio repos).
- [x] Overdue milestones are visually highlighted with red alerts and badges.
