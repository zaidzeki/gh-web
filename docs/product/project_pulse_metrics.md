# PRD: Project Pulse - Strategic Delivery Metrics (DORA)

## 1. Problem Statement
While GH-Web provides excellent **tactical visibility** (real-time CI status, current environment versions, active task triage), it lacks **strategic insight**. Maintainers and team leads cannot easily answer long-term health questions like:
- "How often are we actually deploying?"
- "How long does it take from 'Code Done' to 'Value Delivered'?"
- "Is our deployment stability improving or degrading?"

Without these metrics, teams are flying blind regarding their operational maturity and delivery velocity trends.

## 2. Objectives
- **Quantify Delivery Velocity:** Provide a clear "Deployment Frequency" metric across the portfolio.
- **Measure Lead Time:** Track the time from PR creation/merge to production deployment.
- **Surface Stability Trends:** Calculate the "Change Failure Rate" based on deployment success/failure history.
- **Enable Strategic Benchmarking:** Allow teams to see if they are improving their delivery performance month-over-month.

## 3. User Stories
- **As a Team Lead,** I want to see our monthly deployment frequency so I can report on our delivery velocity to stakeholders.
- **As a Developer,** I want to see the average "Lead Time to Live" for my PRs so I can identify bottlenecks in our review or CI/CD process.
- **As an Ops Engineer,** I want to track our Change Failure Rate so I can determine if our recent infrastructure changes have improved deployment stability.

## 4. Proposed Features

### 4.1. The "Pulse" Dashboard Component
- A new section on the Dashboard (or an expansion of the "Operational Health" view) that displays:
    - **Deployment Frequency:** Number of successful deployments in the last 30 days.
    - **Lead Time to Change:** Median time from PR merge to successful production deployment.
    - **Change Failure Rate:** Percentage of deployments that resulted in a `failure` status.
    - **Time to Restore:** Median time to recover from a `failure` deployment status.

### 4.2. Portfolio Aggregation
- Support for viewing these metrics at both a per-repository level and an aggregated "Team/Org" level.

### 4.3. Visual Trends
- Simple sparklines or "up/down" indicators comparing the current 30-day period to the previous one.

## 5. Acceptance Criteria
- [ ] Backend API `GET /api/repos/<full_name>/pulse` returns DORA metrics for the last 30 days.
- [ ] Metrics are calculated using GitHub's Deployments and Pull Request APIs.
- [ ] Frontend displays the "Pulse" metrics on the Dashboard repository cards (lazy-loaded).
- [ ] Aggregated "Portfolio Pulse" view is available for the active workspace context.

## 6. Technical Considerations
- **Data Depth:** Calculating Lead Time requires matching merged PRs to the deployments that contained their SHAs. This may require scanning up to 100 recent deployments and PRs.
- **Caching:** Pulse metrics should be cached server-side (e.g., for 1 hour) as they are computationally more expensive than real-time health checks.
- **Definition of 'Production':** Reuse the existing "Operational Health" logic for identifying the 'production' environment.
