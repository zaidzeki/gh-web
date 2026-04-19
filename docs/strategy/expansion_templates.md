# 🌅 Horizon: Workspace Templates Expansion Proposal

## 💡 The Pivot
GH-Web currently focuses on managing existing repositories and performing low-level workspace modifications (file uploads, patches). We are pivoting the "Workspace" capability from a simple staging area into a **Scaffolding Engine**. By allowing users to save their workspace state as a named template, we unlock a "Template-to-Repo" flow, enabling rapid bootstrapping of new projects with standardized structures.

## ♻️ The Leverage
This expansion leverages 80% of existing infrastructure:
- **Workspace File Management:** Reuses the existing logic for managing files on the server filesystem.
- **Repository Creation:** Extends the existing `create_repo` API.
- **Archive Extraction:** Reuses the ZIP/Tar extraction logic to apply templates to new repos.

## 🚀 The Delta
- **Template Storage:** A new persistent directory `appdata/.zekiprod/templates/` to store workspace snapshots.
- **Template API:**
  - `POST /api/workspace/save-template`: Snapshots the current workspace.
  - `GET /api/workspace/templates`: Lists available templates.
- **Initialization Logic:** Modifying the `create_repo` flow to optionally pull content from a selected template and push it as the initial commit.

## 🎯 The Impact
- **Developer Productivity:** Instant bootstrapping of repositories with standard boilerplate (CI/CD configs, linting rules, project structure).
- **Standardization:** Teams can define "Gold Templates" for their microservices or documentation repos.
- **Growth:** Positions GH-Web not just as a management tool, but as a project initialization platform.
