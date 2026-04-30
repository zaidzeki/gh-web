# 🌅 Horizon: Unified Task Inbox & Action Center

## 💡 The Pivot
GH-Web currently manages repositories, issues, and PRs in a "Vertical" manner—the user must go to a specific repo or tab to find their work. We are pivoting to a **Horizontal Workflow Orchestration Platform**. By aggregating all actionable items (Assigned Issues, Review Requests, and Owned PRs) into a single **Unified Task Inbox**, we transform GH-Web into a proactive mission control center that tells the user exactly what needs their attention across their entire GitHub portfolio.

## ♻️ The Leverage
- **GitHub Search API:** Uses the powerful `is:open`, `assignee:me`, and `review-requested:me` filters.
- **Issue-Driven Development (IDD):** Leverages existing "Fix" logic to jump from Inbox to Workspace.
- **PR Review Sandboxing:** Leverages existing "Review" logic to jump from Inbox to a collaborative workspace.
- **Contextual Conversations:** Integrates with the Unified Conversation Modal for quick triage.

## 🚀 The Delta
- **Backend:**
    - New `tasks` blueprint.
    - `GET /api/tasks`: Aggregates tasks from three categories:
        1. **Action Required:** PRs where the user is a requested reviewer.
        2. **In Progress:** Issues assigned to the user.
        3. **My PRs:** Open PRs created by the user (surfacing CI status and review state).
- **Frontend:**
    - **Task Inbox Component:** A new prioritized section on the Dashboard.
    - **Smart Actions:** "Fix" button for assigned issues and "Review" button for PRs, directly from the inbox.
    - **Status Indicators:** Surfacing CI failures and "Changes Requested" status to drive urgency.

## 🎯 The Impact
- **Eliminates Fragmented Discovery:** Users no longer need to check 10 repos to find their tasks.
- **Increases Developer Velocity:** One-click transition from "Notification" to "Implementation."
- **Focuses Attention:** Prioritizes items that are blocking others (Review Requests) or blocked by CI (Failing PRs).
