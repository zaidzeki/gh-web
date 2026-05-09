# Architecture: Repository Discovery & Dashboard

## 1. Overview
The Repository Discovery module enables users to explore their GitHub portfolio and monitor active workspaces. It transitions GH-Web from a manual entry tool to a proactive dashboard.

## 2. Components

### 2.1. Discovery Engine
Responsible for fetching repository metadata from the GitHub API using the user's PAT. The engine supports contextual switching between Personal and Organization portfolios.

- **Service:** `app/repos/routes.py`
- **Methods:**
    - Personal: `Github.get_user().get_repos(sort='pushed', direction='desc')`
    - Organization: `Github.get_organization(org_name).get_repos(type='all', sort='pushed')`
- **Metadata Enrichment:** Returns `open_issues_count` and `open_prs_count` to provide a quick summary of pending work.
- **Optimization:**
    - Initial results are limited (top 30) for responsiveness.
    - **Performance Cap:** In large organizations, PR and Issue count aggregation via the Search API is capped at the top 100 most recently updated items to prevent timeouts.

### 2.2. Organization Discovery
Allows the application to discover the collaborative context for the user.
- **Service:** `app/auth/routes.py`
- **Method:** `Github.get_user().get_orgs()`

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
- **Service:** `app/auth/routes.py` or a new `app/user/routes.py`.
- **Method:** `Github.get_user()`

## 3. Data Flow

### 3.1. Dashboard Initialization
1.  Frontend requests `GET /api/user` to display profile info.
2.  Frontend requests `GET /api/user/orgs` to discover available organizational contexts.
3.  Frontend requests `GET /api/repos` (Personal context by default) to list repositories.
4.  Frontend requests `GET /api/workspace/portfolio` to list active workspaces.
5.  UI merges the data: Repositories that are already in the workspace are highlighted with an "Active" badge.

### 3.2. Context Switching
1.  User selects an organization from the Context Switcher in the header.
2.  Frontend updates the `currentContext` state.
3.  Frontend requests `GET /api/repos?org_name=<org_name>`.
4.  Dashboard UI refreshes to show organization-specific repositories and metadata.

### 3.3. Repository Filtering
1.  User types into a search bar.
2.  Frontend performs client-side filtering on the initially loaded 30 repositories.
3.  If no match is found, frontend can trigger a server-side search: `GET /api/repos?search=<query>`.

## 4. Security & Performance
- **Token Usage:** The GitHub PAT is retrieved from the session for every request.
- **Lazy Loading:** Workspace Git status checks (which involve filesystem I/O) should be performed efficiently, possibly caching the result if the folder hasn't been modified.
- **Concurrency:** Ensure that scanning multiple Git repositories in a single request does not block the Flask worker for an extended period.
