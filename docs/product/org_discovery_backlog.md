# Epic: Organization & Team Discovery Backlog

## Overview
This epic aims to resolve the "Organizational Blind Spot" by allowing users to browse and manage repositories within their GitHub Organizations and Teams directly from the GH-Web Dashboard.

## User Stories

### 1. Org List Discovery
**As a developer,** I want to see a list of my GitHub Organizations so that I can select which context I want to browse.
- **Acceptance Criteria:**
  - New API endpoint `GET /api/user/orgs` returns `login` and `avatar_url`.
  - Frontend fetches orgs on login and populates a context selector.

### 2. Contextual Repo Listing
**As a developer,** I want to browse repositories for a specific organization so that I can find professional projects easily.
- **Acceptance Criteria:**
  - `GET /api/repos` accepts an `org` parameter.
  - Selecting an organization in the UI refreshes the repository list with that org's repos.
  - Default view remains the user's personal repositories.

### 3. Quick Action Compatibility
**As a developer,** I want to use the same "Fix", "PR", and "Actions" shortcuts for organizational repos as I do for personal ones.
- **Acceptance Criteria:**
  - All dashboard action buttons (Issues, PRs, Actions, Releases, Clone) correctly target the selected organizational repository.
  - Contextual awareness is maintained when switching tabs.

## Tasks
- [ ] Implement `GET /api/user/orgs` in `app/auth/routes.py`.
- [ ] Update `GET /api/repos` in `app/repos/routes.py` to support `org` filtering.
- [ ] Add context selector dropdown to `app/templates/index.html`.
- [ ] Implement context switching logic in `app/static/js/app.js`.
- [ ] Verify discovery for users with multiple organizations.
