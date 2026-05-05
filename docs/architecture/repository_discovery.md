# Architecture: Repository Discovery & Dashboard

## 1. Overview
The Repository Discovery module enables users to explore their GitHub portfolio and monitor active workspaces. It transitions GH-Web from a manual entry tool to a proactive dashboard.

## 2. Components

### 2.1. Discovery Engine
Responsible for fetching repository metadata from the GitHub API using the user's PAT.
- **Service:** `app/repos/routes.py`
- **Method (Personal):** `Github.get_user().get_repos(sort='pushed', direction='desc')`
- **Method (Organization):** `Github.get_organization(org_name).get_repos(sort='pushed', direction='desc')`
- **Metadata Enrichment:** Returns `open_issues_count` and `open_prs_count` to provide a quick summary of pending work.
- **Scalability Standard:** Aggregation of PR/Issue counts via the Search API is capped at the top 100 most recently updated items to prevent performance degradation in large organizations.
- **Optimization:** Initial results are limited to ensure fast UI loading.

### 2.2. Organization Discovery & Context Management
Handles the identification of GitHub Organizations and maintains the user's active context.
- **Service:** `app/auth/routes.py` or `app/repos/routes.py`.
- **Method:** `Github.get_user().get_orgs()`
- **Caching Strategy:** Discovered organizations are cached in the Flask session to minimize API latency and respect rate limits.
- **Context State:** The active context (`personal` or `org_name`) is maintained in the frontend and passed as a query parameter (`?org_name=...`) to discovery endpoints.

### 2.3. Workspace Portfolio Scanner & Control
Scans the server-side filesystem to identify repositories that have been "sandboxed" or cloned by the user.
- **Service:** `app/workspace/routes.py`
- **Logic:**
    1. Identify the session-specific root: `/tmp/gh-web-workspaces/<session_id>/`.
    2. List all subdirectories.
    3. For each subdirectory containing a `.git` folder, instantiate a `git.Repo` object.
    4. Extract `active_branch`, `is_dirty`, and `ahead`/`behind` counts relative to tracking branches.

## 3. Data Flow

### 3.1. Dashboard Initialization
1.  Frontend requests `GET /api/user` to display profile info.
2.  Frontend requests `GET /api/user/orgs` to populate the context switcher.
3.  Frontend requests `GET /api/repos` (with optional `org_name`) to list repositories.
4.  Frontend requests `GET /api/workspace/portfolio` to list active workspaces.

### 3.2. Context Switching
1.  User selects an organization from the `#orgContextSwitcher` dropdown.
2.  Frontend updates the internal `currentContext`.
3.  Frontend triggers a refresh of all contextual components (Dashboard Repo List, Task Inbox, PR List).

## 4. Security & Performance
- **Token Usage:** The GitHub PAT is retrieved from the session for every request.
- **Search API Optimization:** Using `g.search_issues()` with `user:{login}` or `org:{org_name}` filters for efficient count aggregation.
- **UI Responsiveness:** Context switching uses the `toggleLoading` utility to provide visual feedback during API transitions.
