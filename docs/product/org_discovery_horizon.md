# 🌅 Horizon: Organization & Team Discovery Expansion Proposal

## 💡 The Pivot
GH-Web currently operates in a "Personal-First" mode, fetching only the repositories owned by the authenticated user. However, for professional developers and enterprise teams, the majority of high-value work happens within GitHub Organizations. We are pivoting to **Contextual Discovery**. By introducing an Organization & Team switcher, we transform the dashboard from a personal portfolio into an enterprise-ready "Cockpit" that allows users to manage their work across multiple organizational contexts without leaving the app.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **Dashboard Infrastructure:** Reuses the searchable repository list and active workspace summary.
- **GitHub Search API:** Reuses the metadata aggregation logic (PR/Issue counts) by simply updating the search qualifiers (e.g., from `user:login` to `org:org_name`).
- **Session Management:** Reuses the existing GitHub PAT to discover organizations the user has access to.
- **Unified Task Inbox:** The task inbox logic can be extended to filter by organization context if needed.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Fetches the list of organizations the authenticated user belongs to.
    - Updated `GET /api/repos`: Accepts an optional `org_name` parameter to switch the discovery scope.
- **Frontend:**
    - **Context Switcher:** A searchable dropdown in the application header to toggle between "Personal" and discovered Organizations.
    - **Contextual Persistence:** The selected context is maintained as the user navigates between Dashboard, PRs, and Actions tabs.
- **Performance:**
    - Implements top-100 aggregation caps for organization-scale metadata fetching to maintain dashboard responsiveness.

## 🎯 The Impact
- **Eliminates the "Organizational Blind Spot":** Users can now proactively discover and manage work in company-owned repositories.
- **Enterprise Stickiness:** Positioning GH-Web as a tool for teams rather than just individuals significantly increases its market footprint.
- **Professional UX:** Aligning with standard enterprise patterns (like the GitHub Org Switcher) makes the tool feel like a first-class citizen in a developer's workflow.
