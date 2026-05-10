# Product Backlog: Continuous Delivery & Environment Governance

## Epic: Environment Visibility & Governance
**Description:** Bridge the "Delivery Gap" by integrating GitHub Deployments and Environments into GH-Web, allowing users to track code from PR to Production.

### User Stories

#### 1. Environment Discovery & Monitoring
- **Story:** As a Developer, I want to see a list of my repository's environments so I can monitor what is live in each stage.
- **Acceptance Criteria:**
    - [ ] `GET /api/repos/<full_name>/environments` returns all defined environments.
    - [ ] UI renders "Environment Cards" showing Name, Status (Success/Failure), and Latest Ref (SHA/Tag).
    - [ ] Cards display the "Last Updated" timestamp using the relative `timeAgo` helper.

#### 2. Manual Deployment Dispatch
- **Story:** As an Ops Engineer, I want to manually trigger a deployment to a specific environment so I can control the release timing.
- **Acceptance Criteria:**
    - [ ] "Deploy to..." button opens a modal with the environment pre-filled.
    - [ ] User can specify a Ref (branch, tag, or SHA).
    - [ ] `POST /api/repos/<full_name>/deployments` creates the deployment on GitHub.
    - [ ] UI refreshes after dispatch to show the new pending/in-progress deployment.

#### 3. Deployment History Tracking
- **Story:** As a Product Lead, I want to see a history of deployments for an environment to audit past releases.
- **Acceptance Criteria:**
    - [ ] UI displays a "Deployment History" table below the environment cards.
    - [ ] Table includes Ref, Environment, Status, and Creator.
    - [ ] History is scoped to the selected repository context.

#### 4. Task Inbox Integration (Approvals)
- **Story:** As a Maintainer, I want to see deployments waiting for approval in my Unified Task Inbox.
- **Acceptance Criteria:**
    - [ ] Task Inbox fetches merged PRs with `status:pending` as a proxy for deployment gates.
    - [ ] "Waiting Deployment" tasks are highlighted with a `bg-warning` badge.
    - [ ] "Manage Deploy" action navigates the user directly to the Environments tab for that repository.

### Technical Tasks
- [x] Create `app/deployments` blueprint.
- [x] Implement backend routes for environments and deployments.
- [x] Register blueprint in `app/__init__.py`.
- [x] Update `app/tasks/routes.py` with discovery proxy.
- [x] Create Environments Tab in `index.html`.
- [x] Implement frontend state management and API calls in `app.js`.
- [ ] Add deployment status polling (Future Enhancement).
