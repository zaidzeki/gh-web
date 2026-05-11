# PRD: Operational Health & Delivery Guardrails

## 1. Problem Statement
Users of GH-Web can manage code and trigger deployments, but they lack a high-level view of the *health* of their repositories. After merging a PR or triggering a deployment, they have to manually check the "Actions" or "Environments" tabs to see if things are working or if their intervention (e.g., approval) is required. This "Verification Gap" leads to delayed deployments and reduced confidence in the automated delivery pipeline.

## 2. Objectives
- **Bridge the Verification Gap:** Surface CI/CD health directly on the Dashboard repo list.
- **Enable One-Click Delivery:** Allow users to approve pending deployments directly from their Task Inbox.
- **Proactive Governance:** Identify and highlight repositories that are "failing" or "blocked" without requiring deep-diving into individual tabs.

## 3. User Stories
- **As a Developer,** I want to see if my repository's main branch is passing CI on the dashboard so I know it's safe to start new work.
- **As a Release Manager,** I want to see the "Production" version of each repository at a glance so I can track rollout progress.
- **As an Approver,** I want to be notified of deployments waiting for my review and approve them with a single click from my task inbox.

## 4. Proposed Features

### 4.1. Dashboard Health Badges
- **CI Status Badge:** Enriched repository cards on the dashboard showing the latest status (Success, Failure, Pending) of the default branch.
- **Environment Status Badge:** Displays the current version/ref deployed to the "production" environment (or the most recently updated environment).

### 4.2. Interactive Deployment Reviews
- **Approval Workflow:** Backend support for approving or rejecting deployments that are held by environment protection rules.
- **Task Inbox Integration:** A new category or enrichment for "Waiting Deployment" tasks that includes an "Approve" button if the user has review permissions.

### 4.3. Health-Aware Portfolio
- **Filter by Health:** Ability to filter the repository list to show only failing or pending projects.

## 5. Acceptance Criteria
- [ ] `GET /api/repos` returns `ci_status` for the default branch of the first 30 repositories.
- [ ] `GET /api/repos` returns `production_status` (name, state, ref) for repositories with environments.
- [ ] Dashboard Repo List displays CI status (colored badge) and Production ref.
- [ ] `POST /api/repos/<full_name>/deployments/<id>/review` endpoint is implemented.
- [ ] Task Inbox displays "Approve" button for deployments in a `waiting` state.

## 6. Technical Considerations
- **Performance:** Fetching statuses for 30 repos is expensive. The backend should implement a parallel fetching strategy or the frontend should lazy-load these attributes.
- **GitHub API Versioning:** Deployment reviews require the `ant-man` or `flash` previews (or standard v3 if fully out of preview). PyGithub 2.0+ handles this.
