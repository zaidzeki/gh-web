# 🌅 Horizon: Collaborative Scaffolding Expansion Proposal

## 💡 The Pivot
GH-Web's template system is currently a powerful but "single-player" experience. Templates created from workspaces are stored locally on the server, making them inaccessible to teams or the broader community. We are pivoting to **Collaborative Scaffolding**. By allowing users to "Publish" their local templates back to GitHub as first-class repositories, we transform the template library from a private staging area into a shared platform for organizational standards and community boilerplate.

## ♻️ The Leverage
- **Workspace Template Engine:** Reuses the existing logic for saving and listing local templates.
- **Repository Creation API:** Reuses the `POST /api/repos` backend logic for creating new GitHub repositories.
- **Git Engine:** Reuses `GitPython` to initialize, commit, and push template contents to the newly created remote.
- **UI Consistency:** Adds a simple "Publish" action to the existing Template Library table.

## 🚀 The Delta
- **Backend:**
    - `POST /api/workspace/templates/<template_name>/publish`: A new endpoint that creates a GitHub repository and pushes the local template content to it.
- **Frontend:**
    - **Publish Action:** Added a "Publish" button to each template in the Template Library.
    - **Publish Workflow:** A lightweight interaction that confirms the repository name and visibility before pushing.

## 🎯 The Impact
- **Network Effects:** Sharing templates encourages team-wide adoption of GH-Web as the standard for project initialization.
- **Ecosystem Growth:** Published templates can be "Imported" by other GH-Web users, creating a virtuous cycle of discovery and reuse.
- **Platform Maturity:** Moving from "Local Utility" to "Collaborative Platform" increases the strategic value of the product for enterprise and open-source teams.
