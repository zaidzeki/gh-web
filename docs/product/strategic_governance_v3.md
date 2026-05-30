# PRD: Strategic Governance Phase 3 - Policy Guardrails & Modernization Pulse

## 1. Problem Statement
GH-Web has achieved transparency into tactical health (CI/CD) and strategic pulse (DORA). However, the platform remains **passive**. High-velocity teams can still merge code that violates security policies, and there is no visibility into "Remediation Velocity" (how fast we fix what we break) or "Dependency Freshness" (how far we are behind the latest stable frameworks). Without these, "Elite" DORA scores can mask growing strategic debt.

## 2. Objectives
- **From Passive to Active Governance:** Introduce a Policy Engine that can enforce "Merge Guardrails" based on security severity.
- **Quantify Remediation Velocity:** Calculate Mean Time to Remediation (MTTR) for security vulnerabilities.
- **Measure Strategic Debt:** Track "Dependency Freshness" to identify repositories running on outdated or end-of-life frameworks.

## 3. User Stories
- **As a Security Officer,** I want to define a policy that blocks PR merges if there are open 'Critical' Dependabot alerts, so that we don't deploy known vulnerabilities.
- **As a Team Lead,** I want to see our Security MTTR in the Pulse dashboard so I can improve our response time to new threats.
- **As an Architect,** I want to see a "Freshness" score for my portfolio so I can prioritize framework upgrade sprints before versions go EOL.

## 4. Proposed Features

### 4.1. The Policy Engine (Merge Guardrails)
- Allow users to define simple, repo-level policies (stored in a `governance.json` or similar).
- Initial Policies:
    - `block_merge_on_critical_security`: Prevents merging PRs if the repo has > 0 critical alerts.
    - `block_merge_on_failing_ci`: Strict enforcement of CI success.
- UI: Display "Policy Blocked" indicators on PR and Dashboard cards.

### 4.2. Remediation Pulse (MTTR)
- Extend `GET /api/repos/<full_name>/pulse` to include **Security MTTR**.
- Calculation: Average time from alert creation to alert 'fixed' state for alerts closed in the last 30 days.

### 4.3. Modernization Pulse (Dependency Freshness)
- Analyze `requirements.txt`, `package.json`, or `go.mod` in the workspace to compare current versions against latest stable.
- Provide a "Freshness Index" (0-100%) based on the delta between current and latest versions.

### 4.4. Portfolio Policy Overview
- A new "Governance" view on the Dashboard summarizing policy compliance across the portfolio.
- Heatmap of "Debt" (MTTR vs. Freshness).

## 5. Acceptance Criteria
- [ ] Backend API supports `GET /api/repos/<full_name>/governance/policy` to retrieve and evaluate rules.
- [ ] Pulse API includes `security_mttr_hours` and `dependency_freshness_index`.
- [ ] UI displays "Policy Status" (Compliant/Non-Compliant) on repository cards.
- [ ] Merge button is disabled or visually warned if policies are violated.

## 6. Technical Considerations
- **Version Analysis:** Freshness tracking requires an external service or a local cache of "Latest Versions" (e.g., from PyPI/NPM).
- **Policy Storage:** For the MVP, store policy state in the session or a server-side config file, with a future goal of storing it in the `.github` directory of the repo itself.
- **MTTR Depth:** Calculating MTTR requires fetching "Closed" alerts, which may increase API consumption.
