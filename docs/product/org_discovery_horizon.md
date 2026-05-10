# 🌅 Horizon: Organization & Team Discovery

## 💡 The Pivot
GH-Web currently operates in a "Personal Portfolio" mode, focusing solely on the repositories owned by the authenticated user. We are pivoting to an **Enterprise Control Center**. By introducing Organization Discovery and Context Switching, we allow users to navigate their professional landscape with the same ease as their personal projects. This transforms GH-Web from a developer's utility into a team's orchestrator.

## ♻️ The Leverage
- **GitHub API:** Reuses `PyGithub`'s ability to fetch organizations and organization repositories.
- **Repository Discovery Engine:** Reuses the existing `GET /api/repos` structure and metadata enrichment logic.
- **Dashboard UI:** Reuses the existing repository list component and search filtering.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Discovers the organizations the user belongs to.
    - `GET /api/repos?org_name=...`: Fetches repositories for a specific org, with optimized PR/Issue count aggregation (capped at top 100 most recent to ensure enterprise performance).
- **Frontend:**
    - **Context Switcher:** A dropdown in the header allowing users to switch between "Personal" and various GitHub Organizations.
    - **Contextual State:** Persisting the selected context in the UI session to ensure all discovery actions are scoped correctly.

## 🎯 The Impact
- **Enterprise Ready:** Positions GH-Web as a tool for professional teams and large-scale organizations.
- **Reduced Noise:** Allows users to focus on a specific organizational context, reducing the clutter of a massive portfolio.
- **Strategic Continuity:** Bridges the gap between "Personal" and "Work" environments within a single dashboard.
