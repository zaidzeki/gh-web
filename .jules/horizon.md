## 2025-05-23 - [Expansion: Workspace Templates]
**Learning:** The existing workspace structure, designed for temporary staging, is perfectly suited for a template scaffolding system because it already handles complex file operations and git state. Mapping "local server state" to "reusable project boilerplate" is a high-leverage pivot.
**Action:** Always look for ways to turn "temporary staging data" into "reusable assets" in future expansions.

## 2025-05-24 - [Expansion: Workspace Composition & Cloud IDE]
**Learning:** Repurposing the workspace from a simple Git staging area into a composable environment (multiple templates) and an editor (direct file writing) turns the tool into a creation engine. The adjacency between "management" and "scaffolding" is high because users often need to inject boilerplate into existing repos, not just start new ones.
**Action:** Explore more "compositional" features where multiple modular assets can be combined in a single session.

## 2026-04-21 - [Expansion: PR-to-Workspace Sandboxing]
**Learning:** The "Workspace" is currently a destination for local changes but isolated from the "Pull Request" flow. Connecting them by allowing PR diffs to be applied as "Live Patches" transforms the workspace into a powerful code review and staging environment.
**Action:** Always look for ways to "bridge" existing isolated modules (PRs and Workspaces) to create unified workflows.

## 2026-04-21 - [Expansion: Dynamic Scaffolding]
**Learning:** Static templates are a "dead end" for complex projects that require customization (names, ports, IDs). Adding dynamic parameter injection (via Jinja2) during template application turns simple boilerplate into a flexible project generator.
**Action:** Repurpose existing file-copy logic by adding a "Transformation" layer to multiply the value of stored assets.

## 2026-04-23 - [Expansion: Dynamic Scaffolding Implementation]
**Learning:** By integrating a transformation layer (Jinja2) into both repository creation and workspace composition, we've turned a static "cloner" into a powerful "generator". The leverage here was reusing 90% of the existing file traversal and safety logic, while adding a small but high-impact rendering step.
**Action:** Always ensure that new "Transformation" layers are applied consistently across all entry points (e.g., both Create Repo and Apply Template) to maximize utility.

## 2026-05-24 - [Expansion: Repository Discovery & Dashboard]
**Learning:** The "Manual Entry Wall" was a major friction point where users were treated like command-line operators. Pivoting to a Dashboard-First UX by fetching the user's GitHub portfolio and scanning active workspaces turns the app into a "Control Center". Reusing 90% of existing auth and Git logic unlocked a "Platform-like" feel with minimal code delta.
**Action:** Always prioritize "Discovery over Manual Entry" to reduce friction and increase stickiness.

## 2026-06-15 - [Expansion: Issue Management & Triage]
**Learning:** Expanding from code-centric operations (PRs, Workspaces) into task-centric operations (Issues) completes the project lifecycle within the application. The leverage was high because it reused the existing auth and repository context while providing a high-frequency "triage" use case that increases daily active value.
**Action:** Look for "upstream" (Issues) or "downstream" (Deployments, Actions) adjacencies to bridge lifecycle gaps in the user journey.

## 2026-04-27 - [Expansion: Workspace Omni-Search]
**Learning:** Navigating a hierarchical file tree is a "dead end" for large-scale code discovery. Pivoting to a "Search-First Navigation" model by leveraging native high-performance tools like `ripgrep` turns the workspace into an actionable knowledge base. The leverage was high because it reused the existing Editor and Workspace infrastructure to provide an IDE-like jumping capability.
**Action:** Always consider how native CLI power-tools (rg, fd, fzf) can be exposed via simple web APIs to multiply the value of existing data models.

## 2026-04-30 - [Expansion: Portfolio Health & Governance]
**Learning:** The 'Portfolio' list was previously a "dead end" representing only disk usage. By enriching it with local Git divergence (ahead/behind) and linking it to the session-based IDD context (active Issue/PR), we've pivoted the view from simple management to proactive repository governance. Surfacing CI status directly in the active workspace completes the "triage-to-health" feedback loop.
**Action:** Always look for ways to decorate "List" views with real-time metadata from adjacent systems (Git, GitHub API, Session context) to transform static containers into actionable dashboards.
