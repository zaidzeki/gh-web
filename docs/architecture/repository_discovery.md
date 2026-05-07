# Architecture: Repository Discovery & Dashboard

## 1. Overview
The Repository Discovery module enables users to explore their GitHub portfolio and monitor active workspaces. It transitions GH-Web from a manual entry tool to a proactive dashboard.

## 2. Components

### 2.1. Discovery Engine
Responsible for fetching repository metadata from the GitHub API using the user's PAT.
- **Service:** `app/repos/routes.py`
- **Methods:**
    - **Personal:** `Github.get_user().get_repos(sort='pushed', direction='desc')`
    - **Organization:** `Github.get_organization(org_name).get_repos(sort='pushed', direction='desc')`
- **Organization Discovery:** A new `GET /api/user/orgs` endpoint fetches organizations via `Github.get_user().get_orgs()`.
- **Metadata Enrichment:** Returns `open_issues_count` and `open_prs_count`. For organizations, counts are aggregated using the `search_issues` API scoped to the organization to maintain performance.
- **Optimization:**
    - **Pagination:** Initial results are limited to top 30.
    - **Caching:** Organization lists are cached in the Flask session to reduce API calls during navigation.

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

### 3.1. Dashboard Initialization
1.  Frontend requests `GET /api/user` to display profile info.
2.  Frontend requests `GET /api/user/orgs` to populate the Context Switcher.
3.  Frontend requests `GET /api/repos` (defaulting to Personal) to list repositories.
4.  Frontend requests `GET /api/workspace/portfolio` to list active workspaces.
5.  UI merges the data: Repositories that are already in the workspace are highlighted with a "Open in Workspace" or "Active" badge.

### 3.2. Context Switching & Filtering
1.  **Switch Context:** User selects an Organization from the `#orgContextSwitcher`.
2.  **Fetch Repos:** Frontend triggers `GET /api/repos?org_name=<org_name>`.
3.  **Search:** User types into the search bar.
    - Frontend performs client-side filtering.
    - If no match, frontend triggers `GET /api/repos?search=<query>&org_name=<org_name>`.

## 4. Security & Performance
- **Token Usage:** The GitHub PAT is retrieved from the session for every request.
- **Lazy Loading:** Workspace Git status checks (which involve filesystem I/O) should be performed efficiently, possibly caching the result if the folder hasn't been modified.
- **Concurrency:** Ensure that scanning multiple Git repositories in a single request does not block the Flask worker for an extended period.
