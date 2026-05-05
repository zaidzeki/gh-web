# 🌅 Horizon: Organization & Team Discovery Expansion Proposal

## 💡 The Pivot
GH-Web has successfully transitioned from a manual repository management tool to a personal dashboard. However, for professional and enterprise developers, the bulk of work happens within **GitHub Organizations**. We are pivoting to an **Organization-Aware Dashboard**. By enabling users to switch contexts between personal and organizational repositories, we bridge the "Organizational Blind Spot," transforming GH-Web into an enterprise-grade delivery engine.

## ♻️ The Leverage
- **GitHub Orgs API:** PyGithub provides robust support for listing organizations and member repositories.
- **Context Switcher Pattern:** Reusing the header/navigation space for a searchable dropdown context switcher.
- **Repository Discovery Engine:** Extending the existing `GET /api/repos` logic to support `org_name` filtering.
- **Session Caching:** Leveraging the Flask session to cache organization lists, optimizing performance and API rate limit usage.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Discovers and lists organizations the user belongs to.
    - `GET /api/repos?org_name=<name>`: Filters repository discovery and PR/Issue count aggregation by organization.
    - **Optimization:** Capping Issue/PR search results at 100 items to ensure performance in large organizations.
- **Frontend:**
    - **Context Switcher:** A searchable dropdown in the header to toggle between 'Personal' and various Organizations.
    - **Contextual Refresh:** Automatically refreshing the Dashboard, Tasks, and PRs when the context changes.
- **Architecture:**
    - Implementing a session-based cache for organization metadata.

## 🎯 The Impact
- **Enterprise Ready:** Unlocks the primary use case for professional developers working in shared environments.
- **Operational Efficiency:** Allows users to manage multiple enterprise portfolios without re-authenticating or manual entry.
- **Strategic Growth:** Positions GH-Web as the "Hub" for multi-org repository governance and cross-team collaboration.
