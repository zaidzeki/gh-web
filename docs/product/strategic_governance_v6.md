# PRD: Strategic Governance Phase 6 - Predictive Delivery & Intelligent Remediation

## 1. Problem Statement
The current Strategic Governance implementation provides excellent visibility and reactive controls (SLAs, blocking non-compliant merges). However, it remains "Reactive." Users only know they are failing once a deadline is missed or a violation occurs. There is a "Predictability Gap" where teams cannot easily see which milestones are "At Risk" before they actually fail. Furthermore, as the portfolio grows, "Remediation Fatigue" sets in when users have to manually apply the same security patches across dozens of repositories.

## 2. Objectives
- **Anticipate Failure:** Shift from reactive monitoring to predictive forecasting by surfacing "Delivery Certainty" scores.
- **Scale Remediation:** Introduce "Batch Remediation" to allow one-click patching of common vulnerabilities across the entire portfolio.
- **Intelligent Guardrails:** Implement proactive warnings that trigger when a project's trajectory suggests an upcoming SLA or milestone violation.

## 3. User Stories
- **As a Product Lead,** I want to see a "Certainty Score" for my milestones so I can proactively re-allocate resources before a project falls behind.
- **As a Security Engineer,** I want to apply a critical dependency patch to all 20 of my microservices at once, rather than opening 20 individual workspaces.
- **As a Developer,** I want the system to warn me if my current PR's impact on CI time or complexity puts the milestone's "Elite" DORA status at risk.

## 4. Proposed Features

### 4.1. Delivery Certainty Engine
- **Predictive Scoring:** A machine-learning-inspired (heuristic-based) score that combines:
    - Current Milestone Progress (%)
    - Historical Lead Time (from Pulse API)
    - Time Remaining until Deadline.
- **Visual Forecasting:** Milestones in the Portfolio Roadmap will be color-coded by certainty:
    - **Green (High):** On track to finish >24h before deadline.
    - **Yellow (Medium):** Risk of missing deadline by <15%.
    - **Red (Low):** Velocity suggests milestone will be overdue.

### 4.2. Remediation Orchestrator (Batch Patching)
- **Unified Security Fix:** A new interface that groups repositories by common vulnerabilities (e.g., "Outdated `requests` library").
- **Batch Action:** `POST /api/governance/remediate/batch` which iterates through selected repos, creates branches, applies the patch, and opens PRs in one flow.

### 4.3. Risk Guardrails
- **Dynamic Warnings:** New policy rule `warn_on_at_risk_milestone`.
- **Inbox Integration:** Tasks in the Unified Inbox are tagged with a "Predictive Risk" badge if their parent milestone's certainty score is Low.

## 5. Acceptance Criteria
- [ ] Portfolio Roadmap displays a "Certainty Score" for every milestone.
- [ ] Users can select multiple repositories in the Security Explorer and trigger a batch patch.
- [ ] Task Inbox surfaces "Predictive Risk" warnings for items belonging to at-risk milestones.
- [ ] API supports batch remediation orchestration.

## 6. Technical Considerations
- **Certainty Logic:** `Certainty = Time Remaining / (Remaining Work * Velocity)`.
- **Batch Processing:** Must use `ThreadPoolExecutor` and handle partial failures gracefully (some repos might have merge conflicts during patching).
- **Rate Limiting:** Batch operations must be capped at 20 repos per request to avoid GitHub API secondary rate limits.
