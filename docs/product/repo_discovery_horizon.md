# 🌅 Horizon: Repository Discovery & Portfolio Dashboard Expansion Proposal

## 💡 The Pivot
GH-Web currently operates as a "Command-Line-Style" interface where users must provide the repository name for every action. We are pivoting to a **Dashboard-First UX**. By proactively fetching the user's GitHub portfolio and scanning active server-side workspaces, we transform the application from a manual management tool into a central "Control Center" for their entire GitHub presence.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **Authentication System:** Uses the existing GitHub PAT stored in the session.
- **GitPython Integration:** Reuses the existing Git logic to inspect local workspace state.
- **Flask Route Structure:** Extends the existing blueprints with minimal new API endpoints.
- **Bootstrap UI:** Leverages the existing tabbed interface to introduce a dedicated Dashboard.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user`: Fetches profile info (avatar, login) to personalize the experience.
    - `GET /api/repos`: Lists user's repositories with sorting and search capabilities.
    - `GET /api/workspace/portfolio`: Scans the filesystem to provide a bird's-eye view of all active clones.
- **Frontend:**
    - **Personalized Header:** Displays user avatar and login in the navbar.
    - **The Dashboard:** A new default tab featuring a searchable repo list and an active workspace table.
    - **Discovery-to-Action Bridge:** Clicking a repo in the dashboard automatically populates the target fields in other tabs (PRs, Workspace).

## 🎯 The Impact
- **Eliminates the "Manual Entry Wall":** Users no longer need to remember or copy-paste repository names.
- **Proactive Management:** Surfacing active workspaces prevents "orphan" clones and uncommitted changes from being forgotten.
- **Professional Feel:** Transforming the app into a personalized dashboard increases user stickiness and perceived value.
