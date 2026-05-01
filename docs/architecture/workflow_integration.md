# Architecture: Workflow & CI/CD Integration

## Overview
The Workflow Integration expansion connects the GH-Web frontend to the GitHub Actions subsystem. It provides real-time visibility into CI/CD health and enables manual orchestration of automated tasks.

## Components

### 1. Backend API Layer
New routes will be implemented in a dedicated blueprint `app/actions/routes.py` (to be created) or integrated into `app/repos/routes.py`.

- **Workflow Listing (`GET /api/repos/<full_name>/actions/workflows`)**:
    - Uses `repo.get_workflows()` from PyGithub.
    - Returns workflow names, IDs, and states.

- **Run Monitoring (`GET /api/repos/<full_name>/actions/runs`)**:
    - Uses `repo.get_workflow_runs()`.
    - Returns run status, conclusion, branch, and SHA.
    - Filters can be applied via query parameters (e.g., `status`, `branch`).

- **Manual Dispatch (`POST /api/repos/<full_name>/actions/workflows/<id>/dispatch`)**:
    - Uses `workflow.create_dispatch(ref, inputs)`.
    - Ref default is the repository's default branch or the active workspace branch.

### 2. Frontend Actions Manager
Integrated into `app/static/js/app.js`.

- **Actions Tab**:
    - Features a dual-pane layout: Workflow definitions on the left, Run history on the right.
- **Dynamic Dispatch Form**:
    - A modal that appears when "Run Workflow" is clicked.
    - If a workflow has defined `inputs`, the UI fetches the workflow YAML (or uses a schema if available) to render form fields.
- **Status Indicators**:
    - Visual badges (Success/Fail/Pending) integrated into the Dashboard repository list and Workspace header.

## Data Models & Serialization
The API will standardize the GitHub Actions objects into clean JSON:

**Workflow Run Object:**
```json
{
  "id": 12345,
  "name": "CI Build",
  "status": "completed",
  "conclusion": "success",
  "branch": "main",
  "html_url": "...",
  "updated_at": "ISO-8601"
}
```

## Security & Performance
- **Token Scope:** Operations require the user's PAT to have the `workflow` scope.
- **Rate Limiting:** Actions APIs can be heavy; the frontend should implement polling with a decay (e.g., polling every 10s for active runs, slowing down after 5 minutes).
- **Masking:** Any logs or error messages returned from the Actions API must pass through `mask_token` in the backend.

## Cross-Tab Integration
- **Workspace Tab:** If a commit is pushed, the Workspace header should display the status of the resulting CI run.
- **PR Tab:** PR list items should show the status of the latest "Check Suite" associated with the head commit.
