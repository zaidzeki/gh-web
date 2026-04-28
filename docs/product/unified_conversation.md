# 🌅 Horizon: Unified Conversation & Feedback Loop

## 💡 The Pivot
GH-Web has successfully enabled users to bridge the gap between "identifying an issue" and "implementing a fix" through Issue-Driven Development (IDD) and PR Review Sandboxing. However, the development lifecycle is rarely a straight line; it is a conversation. We are pivoting from a "Transaction-Based" tool to a **"Communication-Centric" Platform**.

By integrating contextual conversations (comments) and formal feedback loops (reviews) directly into the workspace, we eliminate the need for users to switch back to GitHub.com to read feedback or justify their changes. The workspace is no longer just where you code; it's where you collaborate.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **Repository & Issue Context:** Reuses the existing "Active Issue" and "Active Repository" session state.
- **GitHub API Integration:** Leverages `PyGithub`'s comprehensive support for issue/PR comments and pull request reviews.
- **UI Patterns:** Reuses Bootstrap modals and searchable list patterns for the conversation threads.
- **Authentication:** Reuses the session-stored GitHub PAT for authenticated commenting and reviewing.

## 🚀 The Delta
- **Backend:**
    - `GET /api/repos/<full_name>/issues/<number>/comments`: Fetches the entire conversation thread for an issue or pull request.
    - `POST /api/repos/<full_name>/issues/<number>/comments`: Enables posting text replies.
    - `POST /api/repos/<full_name>/prs/<number>/reviews`: Handles formal PR reviews (APPROVE, REQUEST_CHANGES, COMMENT).
- **Frontend:**
    - **Contextual Commenting:** "Comments" button in the Issues and PR tables.
    - **Unified Conversation Modal:** A centralized UI for reading threads and replying, accessible from both Issues and PR tabs.
    - **Review Interface:** A dedicated section within the PR view or Conversation Modal for submitting formal reviews.

## 🎯 The Impact
- **Contextual Flow:** Developers can read reviewer feedback *while* looking at the code in the Workspace.
- **Reduced Context Switching:** Keeps the user focused within the GH-Web ecosystem for the entire development cycle.
- **Engagement:** Increases the "stickiness" of the app by making it the primary interface for both coding and communication.
- **Strategic Alignment:** Solidifies GH-Web as a comprehensive GitHub "Cockpit" that handles both the *work* and the *why*.
