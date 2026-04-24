# RFC: Collaborative PR Contribution 🌅

## 💡 The Pivot
Currently, GH-Web allows reviewers to pull PR code into a sandbox for inspection, but it is largely a read-only experience. We are pivoting this from "Sandbox Review" to **"Collaborative Contribution"**.

By automatically detecting fork permissions and configuring tracking branches, we turn a passive review session into an active development session. Reviewers can now fix bugs, address feedback, or polish code directly in the workspace and push those changes back to the PR author's branch, significantly reducing the turnaround time for landing PRs.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **PR Metadata:** Reuses the enriched PR discovery API that already identifies head repo and branch information.
- **Git Engine:** Reuses `GitPython` multi-remote capabilities and `remote.push()` logic.
- **Authentication:** Reuses the session-stored GitHub PAT for authenticated pushes to both base and fork repositories.
- **UI Architecture:** Reuses the Workspace status badge pattern to provide real-time role feedback (Collaborative vs. Read-Only).

## 🚀 The Delta
- **Backend:**
  - `POST /api/workspace/push`: Refined to use explicit refspecs (`local:remote`) ensuring PR branches are pushed back to their correct source head.
  - `GET /api/workspace/status`: Exposes `can_push` state to the UI based on repository permissions.
- **Frontend:**
  - **Contextual Badging:** Added "Collaborative" and "Read-Only" badges to the PR management table and the Workspace status bar.
  - **Refined Feedback:** Updated status messages to clearly indicate which remote branch is being targeted during a push.

## 🎯 The Impact
- **Velocity:** Drastically reduces the "Review -> Feedback -> Fix -> Review" loop for minor changes.
- **Retention:** Makes GH-Web the preferred tool for maintainers who want to "just fix it" rather than commenting and waiting.
- **Market Adjacency:** Bridges the gap between a "Code Browser" and a "Collaborative IDE," positioning the product for team-based engineering workflows.
