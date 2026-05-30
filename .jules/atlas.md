## 2025-05-23 - [Inauguration]
**Learning:** Initializing the Atlas journal. GH-Web's architecture relies heavily on server-side state for workspaces. While this provides power, it creates a "black box" for the user.
**Action:** Prioritize visibility features (file explorers, status indicators) whenever server-side manipulation is involved to build user trust.

## 2025-05-24 - [Visibility as Trust]
**Learning:** In a 'Cloud IDE Lite' or automated management tool, the user's primary fear is "what did the tool just do to my code?". Providing granular visibility (diffs, history) is not just a feature, it's a security and trust requirement.
**Action:** Every major workspace automation (like template merging or patching) must be accompanied by a 'Review Changes' flow to empower the user.

## 2025-05-25 - [Static vs. Dynamic Assets]
**Learning:** Static templates are a "dead end" for complex projects that require customization. Adding dynamic parameter injection during template application turns simple boilerplate into a flexible project generator, significantly increasing user retention by reducing manual post-creation work.
**Action:** Repurpose existing file-copy logic by adding a "Transformation" layer to multiply the value of stored assets.

## 2025-05-26 - [Beyond Read-Only Reviews]
**Learning:** Streaming a PR via `pull/ID/head` is great for reading, but it's a "collaboration dead-end" because that ref is read-only. To allow users to actually *fix* PRs and push back, we must track the PR's source fork and branch metadata.
**Action:** Enrich PR discovery APIs with fork metadata and update the Workspace engine to manage multiple remotes, enabling a "Review -> Fix -> Push" workflow.

## 2025-05-27 - [The Manual Entry Wall]
**Learning:** Forcing users to manually enter repository names (e.g., `owner/repo`) creates a massive friction point and "Discovery Paralysis." Users shouldn't have to leave the app to find the name of the repo they want to work on.
**Action:** Shift from a "Command-Line" UX to a "Dashboard" UX by implementing repository discovery, starred repo listing, and a central portfolio view for all active workspaces.

## 2025-05-28 - [Actionable Dashboard]
**Learning:** Discovery alone is not enough to break the "Manual Entry Wall". A dashboard that only lists repositories still requires the user to jump between tabs to perform basic maintenance like syncing with remotes or discarding local experiments.
**Action:** Transform the Dashboard from a navigation aid into a "Control Center" by adding quick-action buttons (Sync, Discard) to the Portfolio view and surfacing PR counts in the discovery list to drive prioritization.

## 2025-05-29 - [The Feedback Loop]
**Learning:** Development is not just about moving files; it's about making decisions. A tool that helps you code but forces you to leave to discuss that code is only solving half the problem.
**Action:** Integrate contextual conversations (comments/reviews) directly into the workspace to close the 'Feedback Loop' and keep users focused on collaborative decision-making.

## 2025-05-30 - [The Verification Gap]
**Learning:** Development velocity is meaningless if the code fails silently in production. There is a "Verification Gap" between merging a PR and confirming the health of the deployment. High-trust tools must surface CI/CD status proactively.
**Action:** Expand the 'Control Center' vision to include Workflow Orchestration, enabling users to monitor run history and trigger manual dispatches directly from the GH-Web dashboard.

## 2025-05-31 - [The Delivery Gap]
**Learning:** Releasing a product is just the beginning of its life in production. Users need to know *where* their code is running (Staging, Production) and what version is currently deployed. Without environment visibility, the "Value Delivered" claim remains an assumption.
**Action:** Spec out an Environment Governance module that tracks GitHub Deployments and environments, completing the path from Issue to Production.

## 2025-06-01 - [Scalable Contextual Discovery]
**Learning:** Scalability in an enterprise context requires managing the 'Organizational Blind Spot' without sacrificing performance. Aggregating metadata (PR/Issue counts) across large organizations can lead to API timeouts and rate-limiting.
**Action:** Implement Contextual Switching (Personal vs. Organization) and enforce a "Top 100 Aggregation Cap" on search-based metadata fetching to maintain dashboard responsiveness in enterprise environments.

## 2025-06-02 - [The Operational Blind Spot]
**Learning:** Merging code is only half the battle; ensuring it runs successfully in production is the other half. There is a "Verification Gap" where users lose visibility into the health of their repositories after a merge. High-value management tools must bridge this gap by surfacing real-time CI/CD health and providing interactive governance (e.g., deployment approvals) directly within the development workspace.
**Action:** Prioritize "Operational Health" features that surface branch CI status and environment rollout progress on the main dashboard to provide a full-spectrum delivery overview.

## 2025-06-03 - [Enterprise Noise & Team-Centricity]
**Learning:** In large enterprise organizations, "Organization Filtering" is not enough to bridge the discovery gap. A user's mental model is often tied to their specific Squad or Team, and seeing a flat list of thousands of repositories—even if they belong to the same parent org—causes cognitive overload.
**Action:** Shift from "Org-First" to "Team-First" contextual collaboration by nesting Team discovery within the Organization switcher, enabling a "Team Cockpit" view that filters both repos and tasks.

## 2025-06-04 - [Team-Scoped Discovery Performance]
**Learning:** Aggregating "unassigned" work across an entire team's repository set is performance-prohibitive if the team owns hundreds of repositories. Proactive workload visibility requires a balanced approach between breadth and depth.
**Action:** Implement a "Top 5 Repository Cap" for team-scoped unassigned task discovery to ensure sub-second response times for the Unified Task Inbox while still providing immediate value for a team's core projects.

## 2025-06-05 - [From Task to Goal Governance]
**Learning:** Solving individual tasks (Issues) and code changes (PRs) is the "Inner Loop" of development, but high-velocity teams often lose sight of the "Outer Loop"—the strategic goals. Bridging the 'Strategy Gap' requires moving from task-level management to goal-level governance.
**Action:** Expand the product vision to include Milestone Orchestration, enabling users to group fragmented tasks into cohesive outcomes and track progress against deadlines directly from the dashboard.

## 2025-06-06 - [Portfolio Milestone Aggregation]
**Learning:** Moving from repo-specific to portfolio-level milestone visibility addresses the "Strategy Gap" for users managing multiple projects. However, parallelizing these requests is critical for performance as the portfolio grows to avoid dashboard lag.
**Action:** Always specify parallel execution (e.g. `ThreadPoolExecutor`) in architectural designs for multi-repo aggregation endpoints to ensure scalability.

## 2026-05-23 - [Consolidating Governance Logic]
**Learning:** In a multi-repo dashboard, "Overdue" status must be calculated on the backend to ensure consistency across different UI components (Roadmap cards vs. Task Inbox list). Client-side date comparison leads to "UI Drift" due to timezone discrepancies or stale local clocks.
**Action:** Centralize governance rules (like deadline status) in the backend normalization layer to maintain a single source of truth for project health.

## 2026-05-24 - [From Tactical Visibility to Strategic Pulse]
**Learning:** While surfacing real-time CI status and environment health (Operational Health) is crucial for tactical "now" decisions, teams also need long-term "Pulse" metrics (DORA) to understand their delivery velocity and stability trends. Tactical data tells you "Is it broken now?", but strategic metrics tell you "Are we getting better or worse at delivering?".
**Action:** Extend the "Operational Health" architecture to aggregate historical deployment and PR data, enabling the calculation of DORA metrics (Lead Time, Deployment Frequency) as a baseline for strategic governance.

## 2026-05-25 - [Contextualizing Velocity with Benchmarks & Trends]
**Learning:** Raw DORA metrics (e.g., "5 deployments/month") are meaningless without context. To provide true strategic value, a dashboard must answer: "Is this good?" (Benchmarks) and "Are we improving?" (Trends). 2024 DORA research provides clear performance clusters (Elite, High, Medium, Low) that transform metrics into actionable governance signals.
**Action:** Always pair DORA metric implementations with period-over-period trend analysis and industry-standard performance tiering to bridge the 'Strategic Insight Gap'.

## 2026-05-26 - [From Strategic Delivery to Secure Delivery]
**Learning:** Strategic delivery metrics (DORA) and tactical health (CI/CD) provide a "Velocity and Stability" view, but ignore "Security Integrity". A high-velocity team that deploys critical vulnerabilities or exposed secrets is not "Elite"—it's "At Risk". True governance requires a "Secure Operational Health" view that elevates vulnerability management from a secondary tab to a primary dashboard signal.
**Action:** Pivot the operational health architecture to include a "Security Health" score, ensuring that critical vulnerabilities block the "Success" status of a repository regardless of CI/CD state.

## 2026-05-27 - [Transparency vs. Visibility]
**Learning:** Surfacing a "shield" badge for security health provides *visibility*, but without a way to inspect the underlying alerts, it creates "Action Paralysis." Users see a red badge but don't know if they are facing a catastrophic secret leak or a low-risk dependency update. High-trust governance requires *transparency*—the ability to drill down into the "why" behind the status.
**Action:** Implement a Security Alert Explorer to transform abstract health scores into actionable remediation tasks.

## 2026-05-28 - [Sustainable & Secure Velocity]
**Learning:** High delivery velocity (DORA) is a vanity metric if it's built on a foundation of critical vulnerabilities and aging dependencies. To be truly "Elite," a team must demonstrate high "Remediation Velocity" (MTTR) and maintain "Dependency Freshness." Strategic governance must evolve to identify when tactical speed is causing strategic debt.
**Action:** Spec out a Governance Policy Engine that can enforce quality/security guardrails and extend Project Pulse to track MTTR and framework modernization.
