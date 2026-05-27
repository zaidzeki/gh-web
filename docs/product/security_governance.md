# PRD: Security Governance & Vulnerability Management

## 1. Problem Statement
In modern software development, "Delivery" is not complete unless it is **Secure Delivery**. While GH-Web provides visibility into operational health (CI/CD) and strategic pulse (DORA), it currently has a blind spot regarding **Security Health**. Maintainers cannot see if their repositories have critical vulnerabilities (Dependabot), exposed secrets, or code quality issues without leaving the dashboard and navigating deep into GitHub's Security tab.

## 2. Objectives
- **Centralize Security Visibility:** Surface Dependabot alerts and Security Scanning results directly on the GH-Web dashboard.
- **Drive Proactive Remediation:** Enable maintainers to prioritize security fixes alongside tactical tasks and strategic goals.
- **Close the "Security Gap":** Transform GH-Web into a "Secure Delivery Engine" where security is a first-class citizen of project health.

## 3. User Stories
- **As a Lead Maintainer,** I want to see a count of critical security vulnerabilities on my repository cards so I can prioritize security patches.
- **As a Developer,** I want to see Dependabot alerts in my Unified Task Inbox so I can resolve them as part of my daily workflow.
- **As a Security Lead,** I want a portfolio-wide view of security health to identify which projects are at the highest risk.

## 4. Proposed Features

### 4.1. Security Health Badges
- Add security status badges to Repository Cards on the Dashboard.
- Indicators for:
    - **Vulnerabilities:** Count of open Dependabot alerts (color-coded by severity: Critical/High/Medium/Low).
    - **Secret Scanning:** Alert if active secrets are detected.
    - **Code Scanning:** Status of recent static analysis (CodeQL, etc.).

### 4.2. Security Task Integration
- Integrate Dependabot alerts into the **Unified Task Inbox**.
- Allow users to view alert details and potentially trigger automated "Fix PR" generation (via GitHub's native Dependabot functionality).

### 4.3. Portfolio Security Overview
- A new "Security" view or an expansion of the "Portfolio Health" dashboard section.
- Aggregated counts of vulnerabilities across all active workspaces.
- "At Risk" repository ranking based on alert severity and count.

## 5. Acceptance Criteria
- [ ] Backend API `GET /api/repos/<full_name>/security/alerts` returns Dependabot, Secret Scanning, and Code Scanning alerts.
- [ ] Repository cards on the Dashboard display color-coded security badges.
- [ ] The Unified Task Inbox includes a "Security" category for critical vulnerabilities.
- [ ] Portfolio aggregation surfaces the total security risk across all workspaces.

## 6. Technical Considerations
- **API Availability:** Security APIs are often restricted to specific GitHub plans (Enterprise/Public Repos). The system must handle "Feature Not Enabled" responses gracefully.
- **Permissions:** Fetching security alerts requires specific scopes in the GitHub PAT. The UI should guide users on missing permissions.
- **Performance:** Security scanning can be slow; use the same parallelization and caching patterns as the "Health" and "Pulse" engines.
