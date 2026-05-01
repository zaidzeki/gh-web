# 🌅 Horizon: Workflow & CI/CD Orchestration Expansion Proposal

## 💡 The Pivot
GH-Web has successfully tackled Repository Discovery, Issue Triage, and Workspace Development. However, there is a "Verification Gap" between merging code and it actually running in production. We are pivoting to include **CI/CD Visibility & Control**. By integrating GitHub Actions directly into the dashboard, we transform GH-Web into a high-trust delivery cockpit where users can not only write code but also verify its health and trigger deployment pipelines.

## ♻️ The Leverage
- **GitHub Actions API:** PyGithub provides extensive support for workflows, runs, and dispatches.
- **Unified Repository Context:** Reusing the `full_name` context established across all tabs.
- **UI Consistency:** Reusing the searchable table patterns (from PRs/Issues) for workflow runs and the modal forms for manual dispatches.
- **Session Management:** Reuses the existing GitHub PAT for authorized API calls.

## 🚀 The Delta
- **Backend:**
    - `GET /api/repos/<full_name>/actions/workflows`: Lists defined workflows in the repository.
    - `GET /api/repos/<full_name>/actions/runs`: Lists recent workflow runs with status (success, failure, in_progress).
    - `POST /api/repos/<full_name>/actions/workflows/<workflow_id>/dispatch`: Triggers a manual workflow run (for `workflow_dispatch` events).
- **Frontend:**
    - **Actions Tab:** A dedicated view for monitoring CI/CD health.
    - **Run History Table:** A searchable list of recent runs with direct links to GitHub logs.
    - **Dispatch Modal:** A dynamic form to trigger manual workflows with custom inputs.
    - **Dashboard Integration:** Surfacing the status of the latest "critical" workflow (e.g., CI) in the Repository list.

## 🎯 The Impact
- **Bridges the "Verification Gap":** Developers no longer need to switch to GitHub.com to see if their tests passed.
- **Empowers Non-Technical Stakeholders:** A simplified "Trigger" UI allows team members to run deployments or automation tasks without touching the command line.
- **Professional Maturity:** Positioning GH-Web as a complete Software Delivery Lifecycle (SDLC) tool, covering Discovery, Dev, Review, and now Verify/Deploy.
