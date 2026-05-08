# Architecture: Repository Discovery & Dashboard

## 1. Overview
The Repository Discovery module enables users to explore their GitHub portfolio and monitor active workspaces. It transitions GH-Web from a manual entry tool to a proactive dashboard.

## 2. Components

### 2.1. Discovery Engine
Responsible for fetching repository metadata from the GitHub API using the user's PAT. It supports both "Personal" and "Organization" discovery modes.

- **Service:** `app/repos/routes.py`
- **Discovery Modes:**
    - **Personal:** `Github.get_user().get_repos(sort='pushed', direction='desc')`
    - **Organization:** `Github.get_organization(org_name).get_repos(sort='pushed', direction='desc')`
- **Metadata Enrichment:** Returns `open_issues_count` and `open_prs_count`.
- **Scalability Standard:** In large enterprise contexts, metadata aggregation for Issues and PRs is capped at the **top 100** items (using `g.search_issues`) to maintain dashboard responsiveness.
- **Optimization:** Initial results should be limited (e.g., top 30) to ensure fast UI loading.

### 2.2. Workspace Portfolio Scanner & Control
Scans the server-side filesystem to identify repositories that have been "sandboxed" or cloned by the user, and provides quick maintenance actions.
- **Service:** `app/workspace/routes.py`
- **Logic:**
    1. Identify the session-specific root: `/tmp/gh-web-workspaces/<session_id>/`.
    2. List all subdirectories.
    3. For each subdirectory containing a `.git` folder, instantiate a `git.Repo` object.
    4. Extract `active_branch`, `is_dirty`, and `untracked_files`.
    5. Correlate with GitHub repository names.

### 2.3. User Profile Integration
Fetches the authenticated user's profile to personalize the application.
- **Service:** `app/auth/routes.py` or a new `app/user/routes.py`.
- **Method:** `Github.get_user()`

## 3. Data Flow

### 3.1. Dashboard Initialization & Context Switching
1.  **Identity & Discovery:** Frontend requests `GET /api/user` (Profile) and `GET /api/user/orgs` (Organizations) to populate the context switcher.
2.  **Portfolio Listing:** Frontend requests `GET /api/repos` (Personal) or `GET /api/repos?org_name=<name>` (Org) based on the active switcher context.
3.  **Workspace Portfolio:** Frontend requests `GET /api/workspace/portfolio` to list active workspaces.
4.  **UI Merging:** Repositories that are already in the workspace are highlighted. The selected Organization context is persisted across navigation to the Issues, PRs, and Actions tabs.

### 3.2. Repository Filtering
1.  User types into a search bar.
2.  Frontend performs client-side filtering on the initially loaded 30 repositories.
3.  If no match is found, frontend can trigger a server-side search: `GET /api/repos?search=<query>`.

## 4. Security & Performance
- **Token Usage:** The GitHub PAT is retrieved from the session for every request.
- **Lazy Loading:** Workspace Git status checks (which involve filesystem I/O) should be performed efficiently, possibly caching the result if the folder hasn't been modified.
- **Concurrency:** Ensure that scanning multiple Git repositories in a single request does not block the Flask worker for an extended period.
