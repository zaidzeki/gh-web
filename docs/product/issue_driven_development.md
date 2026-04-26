# Product Specification: Issue-Driven Development (IDD)

## Overview
Issue-Driven Development (IDD) is a feature set that streamlines the transition from identifying a bug or feature request (GitHub Issue) to implementing the fix in the GH-Web Workspace. It centers around the "Fix" action, which automates workspace preparation.

## User Personas
- **The Maintainer:** Needs to quickly triage and address high-priority issues across multiple repositories.
- **The Contributor:** Wants a low-friction way to start working on an issue without complex local environment setup.

## User Stories
- **As a maintainer,** I want to click "Fix" on an issue so that a dedicated branch is created and I am ready to start coding immediately.
- **As a developer,** I want the system to handle repository cloning and branch management automatically so that I can focus on solving the problem.

## Functional Requirements

### 1. The "Fix" Action (Backend)
- **Endpoint:** `POST /api/workspace/setup-issue-fix`
- **Input:** `repo_full_name`, `issue_number`
- **Behavior:**
    1. Check if the repository is already cloned in the workspace. If not, clone it using the session token.
    2. Fetch the latest changes from the default branch.
    3. Create a new branch named `fix/issue-{number}`.
    4. Set the repository as the `active_repo` in the session.
- **Output:** Success message and the branch name.

### 2. The "Fix" Action (Frontend)
- **Location:** Added to each row in the Issues table.
- **UX Flow:**
    1. User clicks "Fix".
    2. Button shows a loading spinner.
    3. On success, the UI navigates to the "Workspace" tab.
    4. The Workspace Explorer refreshes to show the new branch state.

### 3. Context Retention
- The system should recognize when a workspace was activated via a "Fix" action.
- (Phase 2) Pre-fill commit messages with "Closes #{number}".

## Non-Functional Requirements
- **Performance:** Branch creation and workspace activation should complete in under 5 seconds for already-cloned repositories.
- **Security:** Use existing session-based GitHub PATs for all git and API operations.

## Edge Cases
- **Branch Already Exists:** If `fix/issue-{number}` already exists, the system should switch to it rather than failing.
- **Invalid Repo/Issue:** Return a clear error message if the repository or issue cannot be accessed.
- **No Push Permissions:** If the user cannot push to the repository, they can still "Fix" locally, but the UI should indicate "Read-Only Mode" (existing functionality).
