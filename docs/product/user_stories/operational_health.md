# User Stories: Operational Health & Guardrails

## Epic: CI/CD Visibility (The Verification Gap)
*As a developer, I want to see the health of my code immediately after login so that I can prioritize fixes without hunting through multiple tabs.*

### User Story 1: Dashboard CI Badges
- **As a** developer
- **I want to** see a CI status indicator next to each repository on my dashboard
- **So that** I know if the main branch is broken.
- **Acceptance Criteria:**
    - Repository cards in the dashboard list display a color-coded badge for CI status.
    - Statuses: `success` (green), `failure` (red), `pending/running` (yellow/spinning).
    - If no CI is configured, no badge is shown.
    - Data is fetched for the default branch of the repository.

### User Story 2: "What's Live" Indicators
- **As a** product lead
- **I want to** see which version/tag is currently deployed to Production for each repo
- **So that** I can track release progress at a glance.
- **Acceptance Criteria:**
    - Repository cards display the latest successful deployment ref (e.g., `v1.2.0`) for the 'production' environment.
    - If multiple environments exist, prioritize 'production'.
    - Clicking the badge navigates to the Environments tab with that repo selected.

## Epic: Interactive Governance (One-Click Delivery)
*As an approver, I want to unblock deployments from my primary workspace so that I don't lose context by switching to the GitHub web UI.*

### User Story 3: Deployment Approval Actions
- **As a** release manager
- **I want to** approve or reject a pending deployment directly from GH-Web
- **So that** I can maintain delivery velocity.
- **Acceptance Criteria:**
    - Implement a backend endpoint to submit deployment reviews.
    - UI in the Environments tab shows "Approve" and "Reject" buttons for deployments in `waiting` state.
    - A comment can optionally be provided with the review.

### User Story 4: Task Inbox Integration
- **As a** developer with review permissions
- **I want to** see "Waiting for Deployment Approval" tasks in my Unified Inbox
- **So that** I don't miss critical delivery gates.
- **Acceptance Criteria:**
    - The Task Inbox aggregates deployments that are held for approval.
    - The "Deploy" button for these tasks is replaced with an "Approve" button that opens the review modal.
    - Task is removed from the inbox once approved/rejected.
