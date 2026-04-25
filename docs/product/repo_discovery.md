# PRD: Repository Discovery & Portfolio Dashboard

## 1. Problem Statement
GH-Web currently functions as a "point-and-click" tool for specific repositories the user already knows about. It lacks a global overview of the user's GitHub presence, forcing manual entry of repository names and preventing users from seeing the bigger picture of their work (active PRs, clean vs. dirty workspaces, available repositories).

## 2. Objectives
- **Accelerate Discovery:** Allow users to browse and search their own repositories and starred repositories.
- **Surface Actionable Data:** Highlight repositories with open pull requests that require attention.
- **Centralize Workspace Management:** Provide a "Control Center" for all active server-side workspaces.
- **Personalize the Experience:** Show the user's GitHub profile and status to make the application feel like a professional home.

## 3. User Stories
- **As a Developer,** I want to see a list of my most recently active repositories so that I can quickly jump back into my work.
- **As a Maintainer,** I want to see which of my repositories have open PRs so that I can prioritize my review time.
- **As a Power User,** I want to see a list of all my active workspaces and their current Git status (clean/dirty) so that I don't lose track of uncommitted changes.
- **As a New User,** I want to see my GitHub profile and a list of my repositories immediately after login so that I know the app is correctly connected to my account.

## 4. Proposed Features

### 4.1. The Portfolio Dashboard
- **UI:** A new "Dashboard" tab (or a revamped "Repositories" tab).
- **Sections:**
    - **Personal Repositories:** A searchable/filterable list of repos owned by the user, enriched with **open PR counts** to drive prioritization.
    - **Active Workspaces:** A list of repositories currently cloned in the server-side workspace with their branch, status, and **quick actions (Sync, Discard)**.

### 4.2. Repository Discovery API
- **Endpoint:** `GET /api/repos` (with optional `filter=user|starred|org`)
- **Behavior:** Fetches repositories from GitHub using the user's PAT.
- **Metadata:** Includes repo name, description, star count, open issues/PR count, and a flag indicating if a local workspace exists.

### 4.3. User Profile API
- **Endpoint:** `GET /api/user`
- **Behavior:** Returns basic profile info (login, avatar URL, bio) to personalize the UI header.

### 4.4. Workspace Portfolio API
- **Endpoint:** `GET /api/workspace/portfolio`
- **Behavior:** Scans the server-side `/tmp/gh-web-workspaces/<session_id>` directory and returns the status of every active repository.

## 5. Acceptance Criteria
- [ ] Users can see their GitHub avatar and login in the navbar.
- [ ] Users can browse a list of their top 30 repositories without manual entry.
- [ ] Users can search their repositories via a filter input.
- [ ] The dashboard lists all active workspaces with their current branch and "Dirty/Clean" status.
- [ ] Clicking a repository in the list automatically populates it as the target for PR listing or cloning.

## 6. Technical Constraints
- **API Rate Limiting:** Repository fetching should be paginated or limited to prevent hitting GitHub API secondary limits for users with hundreds of repos.
- **Session Isolation:** Workspace portfolio must only list repositories belonging to the current `session_id`.
