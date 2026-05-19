# 🌅 Horizon: Portfolio Roadmap & Cross-Repo Goal Governance

## 💡 The Pivot
While Milestone Orchestration allows users to manage goals within a single repository, most strategic initiatives span across multiple repositories. We are pivoting to **Portfolio Goal Governance**. By aggregating milestones across a user's or team's entire repository set, we provide a unified "Roadmap View." This bridges the "Context Gap," enabling leads and maintainers to see the big picture: how all their projects are tracking towards common deadlines or version releases.

## ♻️ The Leverage
- **Milestone API:** Reusing the backend logic for milestone discovery.
- **Organization/Team Discovery:** Leveraging the team-scoped repository lists to define the roadmap's scope.
- **Unified Task Inbox:** Reusing the aggregation patterns to collect milestones from multiple sources.
- **Health Indicators:** Reusing the overdue/progress calculation logic.

## 🚀 The Delta
- **Backend:**
    - `GET /api/workspace/portfolio/milestones`: Aggregates "Open" milestones from all repositories in the active workspace portfolio.
    - `GET /api/repos/milestones`: (Optional) Bulk fetch for a list of repo full names.
- **Frontend:**
    - **Portfolio Roadmap View:** A new dashboard component or dedicated tab that visualizes aggregated milestones.
    - **Chronological Timeline:** Sorting milestones by due date across all projects.
    - **Cross-Repo Progress Tracking:** High-level progress bars for the entire portfolio.
- **UI Glue (Closing the implementation gap):**
    - Add "Assign Milestone" dropdown/buttons to the main Issues and PRs management tables.
    - Surface milestone badges with completion status directly in task lists.

## 🎯 The Impact
- **Lead-Centricity:** Empowers project leads to manage diverse portfolios with a single glance.
- **Resource Allocation:** Seeing all upcoming deadlines in one timeline helps teams prioritize which repositories need the most attention.
- **Strategic Visualization:** Transforms GH-Web from a "Dev tool" into a "Governance tool."

## 🛠 Error States & Edge Cases
- **Duplicate Titles:** Handling milestones with the same name across different repos (e.g., "v1.0").
- **Different Timezones:** Ensuring consistent due-date rendering.
- **High Volume:** Handling users with hundreds of repos by prioritizing "Active" or "Starred" ones for the roadmap.

## ✅ Acceptance Criteria
- [ ] Users can see a chronological list of milestones across all repositories in their active portfolio.
- [ ] Portfolio milestones include the repository name for context.
- [ ] Users can navigate from a portfolio milestone directly to that repository's focused view.
- [ ] Issues and PRs management tables include UI to assign or change milestones.
