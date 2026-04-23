# PRD: Collaborative PR Contribution

## 1. Problem Statement
The current "PR Review Sandboxing" feature allows users to pull PR code into a workspace for inspection. However, it uses the `pull/ID/head` reference, which is read-only. If a reviewer finds a small bug or wants to suggest a fix, they cannot push their changes directly back to the PR from the workspace. They are forced to switch to a manual local setup, which breaks the "all-in-browser" value proposition of GH-Web.

## 2. Objectives
- **Enable Contribution:** Allow users to modify and push changes back to the PR's source branch.
- **Reduce Friction:** Eliminate the need for reviewers to manually fork and clone repositories for small fixes.
- **Support Collaboration:** Turn GH-Web from a "Review" tool into a "Collaboration" platform.

## 3. User Stories
- **As a Reviewer,** I want to fix a typo or a small bug I found during review directly in the workspace so that I don't have to ask the author to do it.
- **As a Maintainer,** I want to apply a patch to a contributor's PR and push it to their branch so that we can land the PR faster.
- **As a Developer,** I want the workspace to automatically configure the correct remote for the PR's fork so that `git push` just works.

## 4. Proposed Features

### 4.1. Fork-Aware Streaming
- **Behavior:** When streaming a PR, the backend identifies if the PR comes from a fork.
- **Configuration:** The workspace adds a new remote (e.g., `head-fork`) pointing to the fork's URL if it's different from the base repository.
- **Tracking:** The local branch is configured to track the fork's branch.

### 4.2. Authenticated Pushing to Forks
- **Behavior:** The `POST /api/workspace/push` endpoint is updated to support pushing to the fork's remote using the user's PAT.
- **UI:** The push button provides feedback on whether the user has permission to push to the fork.

### 4.3. Metadata Enrichment
- **Endpoint:** `GET /api/repos/<full_name>/prs` is enriched with `head_repo_url` and `head_branch`.

## 5. Acceptance Criteria
- [ ] Users can stream a PR and have the workspace automatically configure a remote for the source fork.
- [ ] Users can commit changes in the workspace and push them back to the PR's source branch (given they have permissions).
- [ ] The UI clearly indicates if a PR is in "Read-Only" mode (due to lack of permissions) or "Collaborative" mode.
- [ ] Security: The system correctly uses the session-stored PAT for authenticated operations on forks.

## 6. Technical Implementation
- **Remote Management:** Use `GitPython` to add and manage remotes: `repo.create_remote('head-fork', fork_url)`.
- **Push Logic:** `repo.git.push('head-fork', 'local-branch:remote-branch')`.
- **Permission Check:** Use `PyGithub` to check if the current user has push access to the head repository.
