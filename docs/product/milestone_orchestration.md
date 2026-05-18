# 🌅 Horizon: Milestone Orchestration & Goal Governance

## 💡 The Pivot
GH-Web has excelled at managing individual tasks (Issues) and code changes (PRs/Workspaces). However, large projects require a higher level of abstraction to track progress towards strategic goals. We are pivoting to **Goal Governance**. By integrating GitHub Milestones, we bridge the "Strategy Gap," allowing users to group tasks into meaningful releases, track velocity against deadlines, and ensure that every individual "Fix" contributes to a larger objective.

## ♻️ The Leverage
- **GitHub Milestones API:** PyGithub provides full support for creating, listing, and updating milestones.
- **Task Linkage:** Reusing the existing Issue/PR infrastructure to associate items with milestones.
- **UI Patterns:** Reusing the card-based dashboard and searchable table patterns.
- **Contextual Awareness:** Extending the Repository context to include active milestone filtering.

## 🚀 The Delta
- **Backend:**
    - `GET /api/repos/<full_name>/milestones`: Lists all milestones with progress stats (open/closed issues).
    - `POST /api/repos/<full_name>/milestones`: Creates a new milestone with title, description, and due date.
    - `POST /api/repos/<full_name>/issues/<number>/milestone`: Assigns an issue/PR to a milestone.
- **Frontend:**
    - **Milestones Tab:** A dedicated view for high-level project planning and tracking.
    - **Milestone Assignment:** Interactive assignment of Issues and PRs to milestones via the Issues/PR tables.
    - **Progress Visualization:** Progress bars for each milestone showing completion percentage.
    - **Goal-Centric Filtering:** Ability to filter the Task Inbox and Issues list by active milestone.
    - **Dashboard Integration:** Repository list enriched with the "Next Milestone" and its due date.

## 🎯 The Impact
- **Strategic Alignment:** Users can see *why* they are working on a task, not just *what* the task is.
- **Predictability:** Surfacing due dates and progress bars helps maintainers manage stakeholder expectations.
- **Completes the Cockpit:** Solidifies GH-Web as a tool for Project Leads and Maintainers, not just individual contributors.

## 🛠 Error States & Edge Cases
- **Overdue Milestones:** Clear visual warnings (red borders/text) for milestones past their due date with open items.
- **Deleted Milestones:** Graceful handling of 404s if a milestone is deleted on GitHub but cached in the UI.
- **API Rate Limits:** Throttling or pagination for repositories with a large number of historic milestones.
- **Empty States:** Encouraging "Create First Milestone" when none exist.

## ✅ Acceptance Criteria
- [x] Users can view a list of milestones for the active repository with progress bars.
- [x] Users can create a new milestone with a title and optional due date.
- [ ] Users can assign Issues and Pull Requests to milestones directly from the management tables.
- [ ] The Task Inbox displays milestone badges for assigned work, highlighting overdue goals.
- [x] The Task Inbox can be filtered by a specific milestone to show goal-specific work.
- [x] The Repository list displays the "Active Milestone" for each repo.
- [x] Backend supports CRUD operations for milestones via PyGithub.
