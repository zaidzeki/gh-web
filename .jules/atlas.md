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

## 2025-06-01 - [The Organizational Blind Spot]
**Learning:** Most professional developers don't work in a vacuum; they work in GitHub Organizations. A tool that only discovers "User Repos" misses the bulk of enterprise work.
**Action:** Update the Repository Discovery engine to include Organization and Team-based repository listing to unlock enterprise value.

## 2025-06-02 - [The Delivery Gap]
**Learning:** A "Release" is not the final state of code; a running environment is. Bridging the gap between the GitHub Release API and the Deployment API is critical for user trust and operational visibility.
**Action:** Spec out an Environment Governance module that tracks GitHub Deployments, enabling users to verify "Live" status directly from the dashboard.
