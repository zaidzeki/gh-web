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

### 4.2. Performance Benchmarking (Tiers)
- Automatically categorize repository performance into **Elite**, **High**, **Medium**, or **Low** tiers based on 2024 DORA benchmarks:
    - **Elite:** Deploy on-demand, Lead time < 1 day, CFR < 15%, Restore < 1 hour.
    - **High:** Deploy daily/weekly, Lead time < 1 week, CFR 16-30%, Restore < 1 day.
    - **Medium:** Deploy weekly/monthly, Lead time < 1 month, CFR 31-45%, Restore < 1 week.
    - **Low:** Deploy > monthly, Lead time > 1 month, CFR > 45%, Restore > 1 week.

### 4.3. Period-over-Period Trends
- Compare the last 30 days of data against the *previous* 30 days (Day 31-60).
- Display "Improving" (Green ↑/↓), "Degrading" (Red ↑/↓), or "Stable" indicators for each metric.

### 4.4. Portfolio Aggregation
- Support for viewing these metrics at both a per-repository level and an aggregated "Team/Org" level.

## 5. Acceptance Criteria
- [x] Backend API `GET /api/repos/<full_name>/pulse` returns DORA metrics for the last 30 days.
- [ ] Backend API supports trend analysis by comparing two 30-day windows.
- [ ] Backend API includes a `tier` classification for each metric and the overall repository.
- [ ] Frontend displays the "Pulse" metrics with color-coded tier badges and trend arrows.
- [x] Metrics are calculated using GitHub's Deployments and Pull Request APIs.
- [ ] Portfolio Pulse includes aggregated trend and tier data.

## 6. Technical Considerations
- **Data Depth:** Calculating Lead Time and Trends requires scanning up to 60 days of history. To maintain performance, limit historical scan to 100 items per window.
- **Trend Inversion:** Ensure logic accounts for "Less is Better" metrics (Lead Time, CFR, Restore) vs. "More is Better" (Frequency).
- **Caching:** Pulse metrics should be cached server-side (e.g., for 1 hour) as they are computationally more expensive than real-time health checks.
- **Definition of 'Production':** Reuse the existing "Operational Health" logic for identifying the 'production' environment.
