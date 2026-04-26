# 🌅 Horizon: Issue Management & Triage Expansion Proposal

## 💡 The Pivot
GH-Web has successfully evolved into a "Control Center" for repository discovery, PR review, and workspace management. However, the lifecycle of a task often begins with an **Issue**. We are pivoting from a "Code-First" management tool to a **Full Lifecycle Lifecycle Management Platform**. By adding Issue triage and creation, we bridge the gap between "identifying a problem" and "implementing a fix" (PR/Workspace), keeping the user entirely within the GH-Web ecosystem.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **Authentication:** Reuses the existing GitHub PAT session.
- **Repository Context:** Reuses the "Active Repository" pattern established by the Dashboard and PR tabs.
- **UI Components:** Reuses the searchable table patterns and modal forms used for PRs and Templates.
- **PyGithub Integration:** Leverages the robust issue management capabilities already present in the `PyGithub` library.

## 🚀 The Delta
- **Backend:**
    - `GET /api/repos/<full_name>/issues`: Lists open issues for a repository.
    - `POST /api/repos/<full_name>/issues`: Allows creating new issues directly from the dashboard.
    - `POST /api/repos/<full_name>/issues/<number>/close`: Enables quick triage by closing resolved or invalid issues.
- **Frontend:**
    - **Issues Tab:** A dedicated view for browsing and managing repository issues.
    - **Triage Actions:** "Close" button for quick cleanup.
    - **Dashboard Integration:** Repository list enriched with a quick link to the Issues tab.

## 🎯 The Impact
- **Completes the Loop:** Users can now go from Issue -> Workspace Fix -> Pull Request -> Merge without leaving the app.
- **Increases Utility for Maintainers:** Triage is a high-frequency task; providing a lightweight interface for it increases the app's daily active value.
- **Strategic Alignment:** Solidifies GH-Web as a comprehensive GitHub "Cockpit" rather than a set of disconnected utilities.
