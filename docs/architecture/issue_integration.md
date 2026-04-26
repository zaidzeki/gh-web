# Architecture: Issue-Driven Development Integration

## Overview
This document describes the technical implementation of the bridge between GitHub Issues and the Workspace environment.

## Components

### 1. Backend Endpoint: `POST /api/workspace/setup-issue-fix`
This endpoint is responsible for preparing the server-side git repository for a specific issue.

- **Sequence:**
    1. **Validation:** Ensure `repo_full_name` and `issue_number` are provided.
    2. **Workspace Selection:** Derive the local directory using `get_workspace_dir(repo_name)`.
    3. **Clone/Refresh:**
        - If the directory doesn't exist or is not a git repo, perform a `git clone`.
        - Otherwise, `git fetch --all`.
    4. **Branch Management:**
        - Identify the default branch (e.g., `main`).
        - Generate the branch name: `fix/issue-{number}`.
        - If the branch already exists locally, checkout to it.
        - If not, create it from the remote default branch (e.g., `origin/main`).
    5. **Session Update:** Set `session['active_repo']` to the repository name.

### 2. Frontend Integration
The frontend utilizes the `app.js` module to handle the transition.

- **Issue Table Update:** The `listIssuesForm` submission handler is updated to render a "Fix" button for each issue row.
- **Navigation Logic:**
    - The `fix-issue-btn` event listener captures the `repo_full_name` and `issue_number`.
    - It triggers the `POST /api/workspace/setup-issue-fix` request.
    - On success, it uses `bootstrap.Tab.getOrCreateInstance(workspaceTab).show()` to switch tabs.
    - It calls `refreshExplorer()` to populate the file tree.

## Data Model Extensions
- **Session:** No new persistent data models are required. The state is maintained via the server-side filesystem (branches) and the existing `active_repo` session key.

## Security
- **Token Usage:** The system reuses the `github_token` from the session for both cloning and branch manipulation.
- **Path Sanitization:** `secure_filename` is used for all repository and branch name components before filesystem operations.
