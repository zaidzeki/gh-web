# Architecture: Repository Discovery & Dashboard

## 1. Overview
The Repository Discovery module enables users to explore their GitHub portfolio and monitor active workspaces. It transitions GH-Web from a manual entry tool to a proactive dashboard.

## 2. Components

### 2.1. Discovery Engine
Responsible for fetching repository metadata from the GitHub API using the user's PAT.
- **Service:** `app/repos/routes.py`
- **Personal Method:** `Github.get_user().get_repos(sort='pushed', direction='desc')`
- **Organization Method:** `Github.get_organization(org_name).get_repos(sort='pushed', direction='desc')`
- **Metadata Enrichment:** Returns `open_issues_count` and `open_prs_count` to provide a quick summary of pending work.
- **Optimization:**
    - Initial results are limited to the top 30 recently pushed repositories.
    - PR and Issue counts are aggregated using the Search API, capped at the top 100 most recently updated items to maintain performance in large organizations.

### 2.2. Workspace Portfolio Scanner & Control
Scans the server-side filesystem to identify repositories that have been "sandboxed" or cloned by the user, and provides quick maintenance actions.
- **Service:** `app/workspace/routes.py`
- **Logic:**
    1. Identify the session-specific root: `/tmp/gh-web-workspaces/<session_id>/`.
    2. List all subdirectories.
    3. For each subdirectory containing a `.git` folder, instantiate a `git.Repo` object.
    4. Extract `active_branch`, `is_dirty`, and `untracked_files`.
    5. Correlate with GitHub repository names.

### 2.3. User Profile & Organization Integration
Fetches the authenticated user's profile and organization memberships to personalize the application and enable context switching.
- **Service:** `app/auth/routes.py`
- **User Method:** `Github.get_user()`
- **Organization Method:** `Github.get_user().get_orgs()`

## 3. Data Flow

### 3.1. Dashboard Initialization
1.  Frontend requests `GET /api/user` to display profile info.
2.  Frontend requests `GET /api/user/orgs` to discover available organizational contexts.
3.  Frontend requests `GET /api/repos` (scoped by `currentContext`) to list repositories.
4.  Frontend requests `GET /api/workspace/portfolio` to list active workspaces.
5.  UI merges the data: Repositories that are already in the workspace are highlighted.

### 3.2. Context Switching
1.  User selects a different context (Personal or an Organization) via the header dropdown.
2.  Frontend updates `currentContext` and triggers a refresh of the repository list and task inbox.

### 3.3. Repository Filtering
1.  User types into a search bar.
2.  Frontend performs client-side filtering on the initially loaded repositories.
3.  If no match is found, frontend can trigger a server-side search: `GET /api/repos?search=<query>&org_name=<context>`.

## 4. Security & Performance
- **Token Usage:** The GitHub PAT is retrieved from the session for every request.
- **Aggregation Caps:** To prevent timeouts in enterprise environments, metadata aggregation (PR/Issue counts) is limited to the 100 most recently updated items.
- **Lazy Loading:** Workspace Git status checks (which involve filesystem I/O) should be performed efficiently.
- **Concurrency:** Ensure that scanning multiple Git repositories in a single request does not block the Flask worker for an extended period.
