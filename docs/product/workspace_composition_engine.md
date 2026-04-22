# 🌅 Horizon: Workspace Composition & Cloud IDE Expansion Proposal

## 💡 The Pivot
GH-Web currently handles "Workspace" as a temporary staging area for basic Git operations and template generation. We are pivoting this capability into a **Workspace Composition Engine** and **Cloud IDE Lite**. Instead of just creating a repo *from* a template, users can now:
1. **Compose:** Merge multiple templates into an active workspace to "layer" features (e.g., merge a 'flask-base' template and then a 'github-actions-ci' template).
2. **Edit:** Modify file content directly in the browser, turning the workspace into a lightweight development environment.
3. **Import:** Pull any public GitHub repository into their personal template library, treating the entire GitHub ecosystem as a source for scaffolding.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **Persistent Template Storage:** Existing `~/.zekiprod/templates/` logic.
- **Git Operations:** Reuses `GitPython` for remote template importing.
- **File System Logic:** Reuses recursive listing and safe-path validation for template merging and file editing.

## 🚀 The Delta
- **Backend:**
  - `POST /api/workspace/apply-template`: A composition endpoint that copies template files into the current workspace without wiping it.
  - `POST /api/workspace/import-template`: An endpoint to clone any GitHub URL into the persistent template library.
  - `POST /api/workspace/files/content`: Extension of the content API to allow `WRITE` operations.
- **Frontend:**
  - **The Editor:** Replacing the static file viewer with a `textarea` based editor.
  - **The Library:** A new "Templates" tab for managing and importing global templates.
  - **Composition UI:** An "Apply Template" action within the Workspace view.

## 🎯 The Impact
- **Ecosystem Integration:** By allowing imports from GitHub, GH-Web becomes a hub for project patterns.
- **Development Velocity:** Direct editing eliminates the "download -> edit -> upload" loop for small changes.
- **Platform Stickiness:** Transforming from a management utility into a creation platform where users define and remix their own "stacks".
