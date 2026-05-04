# Architecture: Repository Discovery & Dashboard

## 1. Overview
The Repository Discovery module enables users to explore their GitHub portfolio and monitor active workspaces. It transitions GH-Web from a manual entry tool to a proactive dashboard.

## 2. Components

### 2.1. Discovery Engine
Responsible for fetching repository metadata from the GitHub API using the user's PAT.
- **Service:** `app/repos/routes.py`
- **Method:** `Github.get_user().get_repos(sort='pushed', direction='desc')`
- **Metadata Enrichment:** Returns `open_issues_count` to provide a quick summary of pending work (PRs and issues).
- **Optimization:** Initial results should be limited (e.g., top 30) to ensure fast UI loading. Subsequent data can be loaded via pagination.

### 2.2. Workspace Portfolio Scanner & Control
Scans the server-side filesystem to identify repositories that have been "sandboxed" or cloned by the user, and provides quick maintenance actions.
- **Service:** `app/workspace/routes.py`
- **Logic:**
    1. Identify the session-specific root: `/tmp/gh-web-workspaces/<session_id>/`.
    2. List all subdirectories.
    3. For each subdirectory containing a `.git` folder, instantiate a `git.Repo` object.
    4. Extract `active_branch`, `is_dirty`, and `untracked_files`.
    5. Correlate with GitHub repository names.

### 2.3. User Profile & Organization Discovery
Fetches the authenticated user's profile and discovered organizations to personalize the experience.
- **Service:** `app/auth/routes.py`
- **User Method:** `Github.get_user()`
- **Organization Method:** `Github.get_user().get_orgs()`
- **Org API:** `GET /api/user/orgs`
    - Returns a list of Org objects: `[{"login": "org1", "avatar_url": "..."}, ...]`.
- **Caching Strategy:**
    - Organization list is cached in the Flask session for 1 hour to prevent redundant API calls during context switching.
    - Repository counts for each Org are fetched lazily and cached.

## 3. Data Flow

### 3.1. Dashboard Initialization
1.  Frontend requests `GET /api/user` to display profile info.
2.  Frontend requests `GET /api/repos` to list the user's GitHub repositories.
3.  Frontend requests `GET /api/workspace/portfolio` to list active workspaces.
4.  UI merges the data: Repositories that are already in the workspace are highlighted with a "Open in Workspace" or "Active" badge.

### 3.2. Repository Filtering
1.  User types into a search bar.
2.  Frontend performs client-side filtering on the initially loaded 30 repositories.
3.  If no match is found, frontend can trigger a server-side search: `GET /api/repos?search=<query>`.

## 4. Security & Performance
- **Token Usage:** The GitHub PAT is retrieved from the session for every request.
- **Lazy Loading:** Workspace Git status checks (which involve filesystem I/O) should be performed efficiently, possibly caching the result if the folder hasn't been modified.
- **Concurrency:** Ensure that scanning multiple Git repositories in a single request does not block the Flask worker for an extended period.
