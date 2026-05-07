# 🌅 Horizon: Organization & Team Discovery Expansion Proposal

## 💡 The Pivot
GH-Web currently centers the user experience around the personal repository space. However, professional developers and open-source contributors primarily work within **GitHub Organizations**. We are pivoting to an **Enterprise-Aware Discovery Model**. By introducing a Context Switcher and organization-aware listing, we address the "Organizational Blind Spot," allowing users to discover and manage work across their entire professional ecosystem without manual context switching on GitHub.com.

## ♻️ The Leverage
- **GitHub Teams & Orgs API:** PyGithub provides full support for listing user organizations and fetching repositories within an organization.
- **Unified Repository Context:** Reuses the existing `full_name` based architecture for PRs, Issues, and Actions.
- **Session Caching:** Reuses the Flask session to cache organization lists, optimizing performance and reducing API rate limiting.
- **Dashboard UI:** Extends the existing searchable list and filter pattern to support organizational context.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Lists all organizations the authenticated user belongs to, including metadata (avatar, description).
    - `GET /api/repos?org_name=<name>`: Filters repository listing to a specific organization.
    - Update `search_issues` logic to include organization-wide PR and Issue counts.
- **Frontend:**
    - **Context Switcher:** A searchable dropdown in the application header (or Dashboard) to toggle between "Personal" and "Organization" views.
    - **Organization Badges:** Visual indicators in the repository list to distinguish between personal and professional projects.
    - **Team-Specific Filtering:** (Future) Ability to filter repositories by specific GitHub Team ownership.

## 🎯 The Impact
- **Professional Relevance:** Positions GH-Web as a primary tool for enterprise workflows.
- **Discovery Velocity:** Dramatically reduces the time required to locate and "Fix" issues across a large organizational portfolio.
- **Unified Visibility:** Provides a single "Command Center" for personal experiments and organizational commitments, bridging the gap between side-projects and day-job.

## 🚶 User Journey: The Enterprise Developer
1. **Login:** User logs in and lands on their Personal Dashboard.
2. **Switch Context:** User clicks the Context Switcher and selects "AcmeCorp."
3. **Discover:** The Dashboard refreshes, showing AcmeCorp's repositories, sorted by most recently pushed.
4. **Action:** User sees a high PR count on `acmeco/core-api`, clicks "Issues", identifies a bug, and clicks "Fix" to start a server-side workspace session immediately.
