# Architecture: PR Contribution Flow

## Overview
This document describes the technical flow for enabling write access to Pull Request source branches within the GH-Web workspace.

## Component Interactions

### 1. PR Discovery (Metadata Enrichment)
When the user lists PRs for a repository, the backend (`app/prs/routes.py`) retrieves additional information for each PR using the GitHub API:
- `head.repo.clone_url`: To identify the fork's location.
- `head.ref`: To identify the source branch name.
- `head.repo.full_name`: To check permissions.

### 2. Fork-Aware Checkout
When a user clicks "Review" on a PR, the `stream-pr` endpoint (`app/workspace/routes.py`) performs the following:
1.  **Detection:** Checks if `head.repo` is different from the base repository.
2.  **Remote Setup:** If a fork is detected, it adds a new remote `head-fork` using the user's PAT for authentication: `https://<token>@github.com/<fork_full_name>.git`.
3.  **Fetch & Track:**
    - Fetches the PR ref: `repo.remotes.origin.fetch(f"pull/{id}/head:review-pr-{id}")`.
    - Configures the local branch to track the fork's branch for pushing: `repo.git.branch("--set-upstream-to", f"head-fork/{head_ref}", f"review-pr-{id}")`.

### 3. Authenticated Push
When the user clicks "Push to Remote" in the workspace:
1.  **Target Selection:** The backend checks if the current branch tracks a `head-fork` remote.
2.  **Push Operation:** It executes a push to the appropriate remote and branch.
3.  **Credential Management:** The push operation uses the session-based PAT, ensuring that no long-term credentials for the fork are stored on the server.

## Security Considerations
- **Permission Scoping:** GH-Web must only attempt to push if the provided PAT has `repo` or `public_repo` scope and the user has been granted access to the fork by the owner (standard GitHub collaboration rules).
- **Token Masking:** Ensure that fork URLs containing the PAT are always masked in logs and error messages.
