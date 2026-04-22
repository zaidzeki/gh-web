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
