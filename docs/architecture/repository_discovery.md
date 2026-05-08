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
- **Optimization:** Initial results should be limited (e.g., top 30) to ensure fast UI loading. Aggregated counts for large organizations are capped at the top 100 items via the Search API.

### 2.2. Organization Discovery Module
Discovers and manages the context of GitHub Organizations the user belongs to.
- **Service:** `app/auth/routes.py`
- **Method:** `Github.get_user().get_orgs()`
- **Frontend Interaction:** Surfaces a Context Switcher dropdown in the Dashboard header.

### 2.3. Workspace Portfolio Scanner & Control
Scans the server-side filesystem to identify repositories that have been "sandboxed" or cloned by the user, and provides quick maintenance actions.
- **Service:** `app/workspace/routes.py`
- **Logic:**
    1. Identify the session-specific root: `/tmp/gh-web-workspaces/<session_id>/`.
    2. List all subdirectories.
    3. For each subdirectory containing a `.git` folder, instantiate a `git.Repo` object.
    4. Extract `active_branch`, `is_dirty`, and `untracked_files`.
    5. Correlate with GitHub repository names.

### 2.4. User Profile Integration
Fetches the authenticated user's profile to personalize the application.
- **Service:** `app/auth/routes.py`.
- **Method:** `Github.get_user()`

## 3. Data Flow

### 3.1. Dashboard Initialization
1.  Frontend requests `GET /api/user` to display profile info.
2.  Frontend requests `GET /api/user/orgs` to discover available contexts.
3.  Frontend requests `GET /api/repos` (defaulting to personal) to list repositories.
4.  Frontend requests `GET /api/workspace/portfolio` to list active workspaces.
5.  UI merges the data: Repositories that are already in the workspace are highlighted with "Active" indicators.

### 3.2. Context Switching
1.  User selects an Organization from the `#orgContextSwitcher`.
2.  Frontend updates the active context and requests `GET /api/repos?org_name=<org_name>`.
3.  Discovery Engine fetches and returns the organization's repositories.
4.  UI refreshes the repository list while maintaining the current workspace and task inbox state.

### 3.3. Repository Filtering
1.  User types into a search bar.
2.  Frontend performs client-side filtering on the initially loaded repositories.
3.  If no match is found, frontend triggers a server-side search: `GET /api/repos?search=<query>&org_name=<optional_org>`.

## 4. Security & Performance
- **Token Usage:** The GitHub PAT is retrieved from the session for every request.
- **Scalability:** For organizations with many repositories, metadata aggregation (PR/Issue counts) uses the Search API with a 100-item cap to prevent N+1 timeouts.
- **Concurrency:** Ensure that scanning multiple Git repositories in a single request does not block the Flask worker for an extended period.
