# 🌅 Horizon: Portfolio Health & Sync Dashboard Expansion Proposal

## 💡 The Pivot
GH-Web currently manages server-side workspaces as isolated clones with basic "dirty/clean" checks. We are pivoting to a **Proactive Portfolio Health Monitor**. By surfacing the synchronization state (Ahead/Behind counts), CI/CD status, and active task context for *all* active workspaces, we transform the dashboard from a simple list into a "Flight Deck" for repository governance.

## ♻️ The Leverage
- **GitPython:** Efficiently calculates branch divergence (ahead/behind) using local metadata.
- **Session Data:** Reuses the `active_issues` session mapping to link workspaces back to their triage context.
- **Combined Status API:** Leverages PyGithub to fetch CI health for the active task.
- **Portfolio Infrastructure:** Extends the existing `workspace_portfolio` scanning logic.

## 🚀 The Delta
- **Backend:**
    - Enrich `/api/workspace/portfolio` with `ahead`/`behind` counts, `last_commit_subject`, and `active_issue` metadata.
    - Implement `POST /api/workspace/sync-all` to fetch updates for all workspaces in a single batch.
    - Enrich `/api/workspace/status` with `ci_status` (success, failure, pending).
- **Frontend:**
    - Enhance Dashboard Workspace list with Ahead (↑) and Behind (↓) badges.
    - Display the active issue/PR title next to the workspace name in the portfolio.
    - Add a "Sync All" button to the Dashboard.
    - Add a live CI status indicator to the Workspace tab header.

## 🎯 The Impact
- **Operational Visibility:** Users can instantly identify which workspaces are stale or have failing builds.
- **Reduced Cognitive Load:** The "Sync All" feature ensures that "Checking for updates" is a one-click operation across all projects.
- **Seamless Continuity:** Bringing the "Active Issue" context back to the Dashboard closes the loop between triage and implementation.
