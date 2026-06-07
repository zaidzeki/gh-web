# PRD: Strategic Governance Phase 6 - Predictive Delivery & Intelligent Remediation (Extended)

## 1. Executive Summary
Strategic Governance Phase 6 closes the "Governance Gap" by moving from reactive SLA tracking to proactive risk mitigation and automated batch remediation. By surfacing Certainty Scores and providing a "Remediation Orchestrator," we empower engineering leaders to identify and fix cross-portfolio debt with minimal manual overhead.

## 2. Problem Statement
Manual remediation of common vulnerabilities (e.g., a critical security patch in a shared library) is time-consuming and error-prone when applied to dozens of microservices. Furthermore, milestones often fail silently until the deadline passes because lead-time and velocity metrics are not integrated into the goal-tracking UI.

## 3. Goals
- **Predictive Risk:** Warn users when milestone trajectory suggests a deadline violation.
- **Batch Remediation:** One-click patching of common Dependabot alerts across multiple repositories.
- **Reduced Friction:** Automated PR creation for security updates.

## 4. User Stories
- **As a Technical Lead,** I want to toggle a "Warn on At-Risk Milestones" policy so that my team is alerted to delivery risks in the Task Inbox.
- **As a Security Engineer,** I want to see which repositories are vulnerable to the same CVE and apply a fix to all of them simultaneously.
- **As a Developer,** I want automated remediation PRs to be clear, descriptive, and linked to the vulnerability they solve.

## 5. Functional Requirements
- **Certainty Policy:** A new `warn_on_at_risk_milestone` rule in the PolicyStore.
- **Risk Visualization:** Integration of "Low Certainty" status into the `evaluate_repo_policy` engine.
- **Remediation Suggestions:** API to aggregate Dependabot alerts by package and version across the portfolio.
- **Batch Executor:** Secure, API-driven patching of `requirements.txt` files and PR creation.

## 6. Acceptance Criteria
- [x] `PolicyStore` supports `warn_on_at_risk_milestone`.
- [x] Task Inbox displays "Predictive Risk" badges based on policy.
- [x] "Batch Remediation" button appears in the Portfolio Security card.
- [x] Remediation Orchestrator Modal displays common vulnerability groups.
- [x] Batch execution creates branches and PRs on GitHub without full repo clones.
