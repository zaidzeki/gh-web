# PRD: Workspace Git Visibility & Transparency

## 1. Problem Statement
The server-side workspace in GH-Web is currently a "black box." Users can perform powerful operations (uploads, patches, template merges), but they lack the visibility to verify exactly *what* changed before they commit or push. This leads to anxiety, potential errors, and a lack of trust in the platform's automation.

## 2. Objectives
- **Build Trust:** Provide users with visual confirmation of changes.
- **Reduce Errors:** Allow users to catch unintended modifications early.
- **Enhance Workflow:** Enable basic Git safety features like diffing and history within the browser.

## 3. User Stories
- **As a Developer,** I want to see a diff of my current workspace changes so that I can verify my work before committing.
- **As a Developer,** I want to view the recent commit history of my workspace so that I can track the evolution of my project.
- **As a Developer,** I want to revert individual file changes or the entire workspace to the last committed state so that I can recover from mistakes.

## 4. Proposed Features

### 4.1. Workspace Diff Viewer
- **UI:** A "View Diff" button in the Workspace Explorer.
- **Behavior:** Opens a modal showing the output of `git diff` for the active workspace.
- **Endpoint:** `GET /api/workspace/diff`

### 4.2. Commit History
- **UI:** A "History" tab or modal showing a list of recent commits.
- **Behavior:** Displays commit hash, author, date, and message (`git log -n 10`).
- **Endpoint:** `GET /api/workspace/history`

### 4.3. Revert Changes
- **UI:** A "Discard Changes" button.
- **Behavior:** Executes `git checkout -- .` (or `git reset --hard`) to return the workspace to a clean state.
- **Endpoint:** `POST /api/workspace/revert`

## 5. Acceptance Criteria
- [ ] Users can retrieve a unified diff of all uncommitted changes via the API.
- [ ] Users can retrieve a list of the last 10 commits via the API.
- [ ] Users can reset their workspace to the `HEAD` state via the API.
- [ ] All new endpoints must enforce `is_safe_path` and verify the workspace is a Git repository.
- [ ] UI provides clear feedback (success/error toasts) for all Git operations.

## 6. Technical Constraints
- Diffs should be limited in size (e.g., max 5000 lines) to prevent browser hang.
- Operations should only be available if the workspace `.git` directory exists.
