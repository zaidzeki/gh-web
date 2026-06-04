# Architectural Design: Phase 6 - Predictive Delivery & Intelligent Remediation

## 1. Overview
Strategic Governance Phase 6 extends the existing `GovernanceAggregationService` and `Pulse` engine to support predictive analytics and batch orchestration. The goal is to provide a "Forecasting Layer" that sits on top of existing metrics.

## 2. Delivery Certainty Engine

### 2.1. Logic & Data Flow
The engine calculates a `CertaintyScore` (0.0 to 1.0) for a given milestone:

1.  **Work Estimation:** `RemainingWork = TotalIssues - ClosedIssues` (within the milestone).
2.  **Velocity Input:** `LeadTimeHours` (calculated by `calculate_repo_pulse`).
3.  **Required Time:** `TimeNeeded = RemainingWork * LeadTimeHours`.
4.  **Available Time:** `TimeRemaining = MilestoneDeadline - CurrentTime`.
5.  **Score Calculation:** `Certainty = TimeRemaining / TimeNeeded`.
    - `Certainty > 1.2` -> **High (Elite)**
    - `Certainty 0.9 - 1.2` -> **Medium (At Risk)**
    - `Certainty < 0.9` -> **Low (Overdue Predicted)**

### 2.2. API Integration
The `GET /api/workspace/portfolio/milestones` endpoint will be updated to include a `certainty_score` and `certainty_tier` in its response payload.

## 3. Remediation Orchestrator (Batch Patching)

### 3.1. Batch Workflow
A new `RemediationOrchestrator` service will handle the `POST /api/governance/remediate/batch` request:

1.  **Validation:** Ensure all target repos are within the user's push permissions.
2.  **Parallelization:** Use `ThreadPoolExecutor` to process repositories concurrently.
3.  **Execution (Per Repo):**
    - Clone (or update) workspace.
    - Create a standard remediation branch `patch/batch-remediation-<timestamp>`.
    - Apply the transformation (e.g., updating a `requirements.txt` entry).
    - Commit and Push.
    - Create a Pull Request with a "Batch Remediation" label.
4.  **Response:** Return a manifest of successes, failures, and created PR URLs.

### 3.2. Error Handling
- **Merge Conflicts:** If a patch cannot be applied cleanly, the operation for that repo is skipped and logged as a failure in the manifest.
- **API Limits:** The orchestrator will enforce a maximum of 20 concurrent operations and include small jitters between requests.

## 4. Intelligent Risk Guardrails

### 4.1. Predictive Task Enrichment
The `tasks` blueprint will be updated to fetch the `CertaintyScore` of a task's parent milestone. If the score is `< 1.0`, the task is enriched with:
- `predictive_risk: "at_risk"`
- `risk_message: "Milestone completion predicted to exceed deadline by X hours."`

## 5. Components Diagram
```
[Frontend Dashboard]
       |
       v
[API Gateway (Flask)]
       |
       +--> [Certainty Engine] <--> [Pulse Engine]
       |          |
       |          +--> [Milestone Service]
       |
       +--> [Remediation Orchestrator] <--> [Workspace Engine]
                  |
                  +--> [GitHub API (Batch PRs)]
```

## 6. Security & Persistence
- **Permissions:** Batch remediation requires explicit push access to every target repository.
- **Audit Logging:** Every batch operation will be recorded in a new `remediation_logs.json` for governance auditing.
