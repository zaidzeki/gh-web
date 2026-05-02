# Architecture: Environment & Deployment Integration

## 1. Overview
The Environment & Deployment module connects GH-Web to GitHub's Deployment API. It provides a visual representation of the repository's target environments (Staging, QA, Production) and tracks the lifecycle of code promotion across these stages.

## 2. Components

### 2.1. Deployment Blueprint (`app/deployments/routes.py`)
A new backend blueprint to handle environment and deployment metadata.

- **Environment Listing (`GET /api/repos/<full_name>/environments`)**:
    - Uses `repo.get_environments()`.
    - Returns environment names, protection rules (e.g., required reviewers), and current deployment status.
- **Deployment History (`GET /api/repos/<full_name>/deployments`)**:
    - Uses `repo.get_deployments()`.
    - Filters by `environment` if provided.
    - For each deployment, fetches its latest status using `deployment.get_statuses()`.
- **Trigger Deployment (`POST /api/repos/<full_name>/deployments`)**:
    - Uses `repo.create_deployment(ref, environment, payload, description)`.
    - `ref` can be a branch name, tag, or specific SHA.

### 2.2. Frontend Environments Manager
Integrated into `app/static/js/app.js` and a new "Environments" tab.

- **Environment Dashboard**:
    - A grid of "Environment Cards".
    - Each card displays the current "Latest Status" (e.g., Success, In Progress, Queued).
    - Displays the metadata for the deployed ref (SHA, Tag name, commit message).
- **Promotion Workflow**:
    - A "Deploy to..." button that opens a modal.
    - The modal allows selecting a target environment and a source ref (defaulting to the latest successful build from the previous environment).
- **Approval Interceptor**:
    - If a deployment is in a `waiting` state (due to environment protection rules), the UI displays an "Approve / Reject" action for users with appropriate permissions.

## 3. Data Models

**Deployment Status Object:**
```json
{
  "id": 98765,
  "environment": "production",
  "state": "success",
  "ref": "v2.1.0",
  "sha": "a1b2c3d4",
  "description": "Deployed via GH-Web",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "creator": "jules-gh"
}
```

## 4. Security & Permissions
- **Deployment Protection:** GH-Web relies on GitHub's native environment protection rules. Approval actions in GH-Web will trigger the corresponding GitHub API calls, which will enforce the user's permissions.
- **Auditing:** Every deployment triggered via GH-Web will include a `GH-Web` identifier in the `payload` or `description` for traceability.

## 5. Performance
- **Status Polling:** Similar to GitHub Actions, the Environments UI will implement a polling strategy for "In Progress" deployments to provide real-time updates without excessive API usage.
- **Prefetching:** Latest environment status will be prefetched and cached during Dashboard initialization to show the "Production Version" badge.
