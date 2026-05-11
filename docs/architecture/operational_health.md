# Architecture: Operational Health & Guardrails

## 1. Overview
This module extends the Repository and Deployment blueprints to provide real-time health visibility and interactive governance. It bridges the gap between code management and operational awareness.

## 2. Backend Extensions

### 2.1. Repository Health API (`app/repos/routes.py`)
To maintain high performance in the main repository list, health data (CI status and Production status) will be offloaded to a dedicated batch endpoint.

- **Endpoint:** `GET /api/repos/health?repos=owner/repo1,owner/repo2...`
- **Optimization:** Uses `concurrent.futures.ThreadPoolExecutor` to fetch status for multiple repositories in parallel. This circumvents the sequential latency of N+1 GitHub API calls.
- **CI Status:** Fetched via `repo.get_combined_status(repo.default_branch)`.
- **Production Status:** Fetched via `repo.get_deployments(environment='production')` (takes the `latest_status` of the first entry).

### 2.2. Deployment Reviews (`app/deployments/routes.py`)
New endpoint to handle deployment approvals, specifically for environments with protection rules.

- **Endpoint:** `POST /api/repos/<path:full_name>/deployments/<int:deployment_id>/review`
- **Method:** `POST`
- **Payload:** `{"state": "approved" | "rejected", "comment": "string"}`
- **Implementation:** Uses `repo.get_deployment(deployment_id).create_review(state=state, comment=comment)`.

### 2.3. Task Inbox Enrichment (`app/tasks/routes.py`)
- **Waiting Deployment Category:** Currently searches for merged PRs with `status:pending`.
- **Interactive Promotion:** The task object will be enriched with a `pending_deployment_id`. If present, the frontend will render an "Approve" action instead of a generic "Deploy" action.

## 3. Frontend Integration

### 3.1. Dashboard UI (Lazy Loading)
- **Lifecycle:**
    1. Dashboard loads repo list via `GET /api/repos`.
    2. Once rendered, the frontend extracts the `full_name` of visible repos.
    3. Triggers a batch request to `GET /api/repos/health`.
    4. Injects health badges into the DOM upon receipt.
- **Badge Components:**
    - `ci-success`, `ci-failure`, `ci-pending` classes.
    - `env-production` badge showing the latest deployed ref.

### 3.2. Task Inbox Actions
- **Approve Modal:** Triggered by "Approve" button in the Task Inbox. Submits to the new deployment review endpoint and refreshes the inbox on success.

## 4. Error Handling & Security
- **Resilience:** Parallel fetching must handle exceptions gracefully. If fetching for one repo fails (e.g., 404 or 403), that specific repo's health object is returned as `{"error": "..."}` or `null`, allowing other results to proceed.
- **Permissions:** GitHub's API enforces environment protection. If a user attempts to approve a deployment they aren't authorized for, the backend passes the 403 error (masked) to the UI.
