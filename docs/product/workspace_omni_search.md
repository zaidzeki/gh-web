# 🌅 Horizon: Workspace Omni-Search Expansion Proposal

## 💡 The Pivot
GH-Web currently relies on a hierarchical file explorer for navigating active workspaces. While effective for small projects, it becomes a bottleneck as codebase complexity grows. We are pivoting to a **Search-First Navigation** model. By introducing an Omni-Search capability, we transform the workspace from a simple file tree into a searchable knowledge base, allowing users to jump directly to code symbols, configurations, or content across the entire repository.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **Active Workspace Context:** Reuses the `active_repo` and session-based directory structure.
- **Security Infrastructure:** Reuses `is_safe_path` for result validation and `mask_token` for error handling.
- **UI Architecture:** Reuses the existing modal patterns and the recently implemented File Editor to turn search results into actionable entry points.
- **Native Tooling:** Leverages the high-performance `ripgrep` (`rg`) utility already available in the sandbox environment.

## 🚀 The Delta
- **Backend:**
    - `GET /api/workspace/search`: A new endpoint that executes a filtered `ripgrep` command against the active workspace and returns a structured list of matches with file paths and line context.
- **Frontend:**
    - **Omni-Search Bar:** A prominent search interface within the Workspace tab.
    - **Results Navigator:** A modal displaying matches that allows users to instantly open the corresponding file and line in the integrated editor.

## 🎯 The Impact
- **Developer Velocity:** Instant navigation significantly reduces the time spent "hunting" for files in large repositories.
- **Discovery:** Enables users to quickly understand how a specific variable, function, or pattern is used across a new project.
- **Modern IDE Feel:** Bridges the gap between a simple web-based management tool and a professional development environment.
