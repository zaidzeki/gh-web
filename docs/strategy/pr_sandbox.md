# 🌅 Horizon: PR Review Sandbox Expansion Proposal

## 💡 The Pivot
GH-Web currently treats "Pull Requests" and "Workspaces" as separate concerns. We are pivoting this by introducing **PR Review Sandboxing**. This allows users to instantly pull a Pull Request's code into their active workspace for live review, testing, and modification. Instead of just reading code on GitHub, the workspace becomes a "Safe Sandbox" where PRs can be experienced and validated in a real environment.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **PR Discovery:** Existing `GET /api/repos/<full_name>/prs` logic.
- **Workspace Isolation:** Existing session-based `/tmp/gh-web-workspaces/` infrastructure.
- **Git Engine:** Reuses `GitPython` logic for fetching remote refs and managing branches.

## 🚀 The Delta
- **Backend:**
  - `POST /api/workspace/stream-pr`: A new endpoint that automates the `fetch` and `checkout` of a PR head into the workspace.
- **Frontend:**
  - **Review Action:** A new "Review" button in the Pull Request table.
  - **Automatic Context Switching:** Logic to switch to the Workspace tab and refresh the explorer upon "Review" click.

## 🎯 The Impact
- **Streamlined Review:** Eliminates the manual `git fetch origin pull/ID/head:branch` steps for reviewers.
- **Confidence:** Allows reviewers to actually *run* or *build* the PR code in the server-side workspace before approval.
- **Collaboration:** Users can apply their own patches on top of a PR and push them back, turning review into a truly collaborative session.
