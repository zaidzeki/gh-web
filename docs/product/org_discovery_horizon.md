# 🌅 Horizon: Organization & Team Discovery Expansion Proposal

## 💡 The Pivot
GH-Web has successfully transformed into a "Dashboard-First" management tool for personal GitHub portfolios. However, professional development almost always happens within a collaborative context—specifically **GitHub Organizations**. We are pivoting to an **Enterprise-Ready Contextual UX**. By introducing Organization and Team discovery, we bridge the "Organizational Blind Spot," allowing users to switch contexts and manage their professional work with the same ease as their personal projects.

## ♻️ The Leverage
- **GitHub Orgs API:** PyGithub provides full support for listing user organizations and their repositories.
- **Unified Dashboard Patterns:** Reusing the searchable repository list and portfolio summary from the personal dashboard.
- **Search API Efficiency:** Reusing the search-based PR and Issue count aggregation logic, but scoped to organization contexts.
- **Frontend State Management:** Extending the current dashboard state to support a `currentContext` filter.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Fetches the list of organizations the user belongs to.
    - `GET /api/repos?org_name=<org>`: Filters the repository list to a specific organization.
    - **Performance Cap:** Aggregating PR/Issue counts for large organizations is capped at the top 100 most recently updated items to prevent timeouts.
- **Frontend:**
    - **Context Switcher:** A searchable dropdown in the application header (replacing or augmenting the static profile view).
    - **Contextual Filtering:** Switching organizations updates the Repository list, active workspaces (filtered by repo owner), and the Task Inbox.
    - **Organization Avatars:** Visual indicators in the switcher to help users quickly identify the correct context.

## 🎯 The Impact
- **Enterprise ROI:** Unlocks GH-Web for use in professional environments (agencies, open-source orgs, corporate teams).
- **Reduced Clutter:** Users can focus on "Work" repos during the day and "Personal" repos in the evening without a giant, flat list.
- **Scalable Discovery:** The contextual approach prevents the dashboard from becoming unusable as the total number of accessible repositories grows.

## User Stories
- **As a Developer,** I want to switch to my company's GitHub Organization context so I can see only the repositories relevant to my current project.
- **As a Team Lead,** I want to see the PR and Issue counts across all repos in our organization so I can prioritize triage.
- **As a Contributor,** I want my Task Inbox to reflect my work within a specific organization when I have that context selected.

## Acceptance Criteria
- [ ] User can view a list of their GitHub Organizations in a dropdown.
- [ ] Selecting an organization updates the repository discovery list.
- [ ] The "Personal" context remains available as the default view.
- [ ] Repository metadata (PR/Issue counts) is correctly aggregated for organization repos.
- [ ] Large organization aggregation is capped at 100 items to maintain performance.
