# 🌅 Horizon: Continuous Delivery & Environment Governance

## 💡 The Pivot
GH-Web has mastered the path from Issue to Release. However, the final destination of code is not a "Release" object on GitHub—it's a running environment. We are pivoting to include **Environment Governance**. By integrating GitHub Deployments and Environments, we bridge the "Delivery Gap", providing users with visibility into *where* their code is deployed (Staging, Production) and the ability to promote releases across environments directly from GH-Web.

## ♻️ The Leverage
- **GitHub Deployments API:** PyGithub provides full support for creating and listing deployments and deployment statuses.
- **Unified Repository Context:** Reusing the `full_name` context and authentication session.
- **UI Patterns:** Reusing the list-group and modal form patterns from the Releases and Actions tabs.
- **Task Inbox Integration:** Surfacing "Waiting for Approval" deployment notifications.

## 🚀 The Delta
- **Backend:**
    - `GET /api/repos/<full_name>/environments`: Lists defined environments and their current protection rules.
    - `GET /api/repos/<full_name>/deployments`: Lists recent deployment history per environment.
    - `POST /api/repos/<full_name>/deployments`: Creates a new deployment (e.g., deploying a specific Tag or SHA to 'production').
- **Frontend:**
    - **Environments Tab:** A dedicated view for monitoring environment health and deployment status.
    - **Environment Cards:** Visual cards showing "What's Live" in each environment (Version, SHA, Last Updated).
    - **Deployment Orchestrator:** A form to trigger deployments or approvals.
    - **Dashboard Integration:** Surfacing "Production Version" in the Repository list.

## 🎯 The Impact
- **Closes the "Value Loop":** Developers and stakeholders can confirm that their fixes are actually "Live".
- **Reduces Production Anxiety:** Providing a clear, audit-able history of deployments within the management tool.
- **Strategic Positioning:** Completes the transformation of GH-Web into a full-spectrum DevOps platform covering Triage, Dev, Review, Verify, Release, and now **Operate**.

## User Stories
- **As a Developer,** I want to see if my merged PR has been deployed to the Staging environment so I can perform final verification.
- **As a Product Lead,** I want to see which version is currently in Production so I can coordinate with marketing and support.
- **As an Ops Engineer,** I want to approve pending deployments to restricted environments directly from my task inbox.
