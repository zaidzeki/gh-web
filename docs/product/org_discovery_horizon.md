# 🌅 Horizon: Organization & Team Discovery

## 💡 The Pivot
GH-Web currently focuses on the individual developer's personal repository portfolio. We are pivoting to an **Enterprise-Ready Platform** by introducing **Organization & Team Discovery**. By allowing users to switch contexts between their personal account and various discovered GitHub Organizations, we bridge the "Organizational Blind Spot", transforming the dashboard into a unified cockpit for professional, collaborative, and personal work.

## ♻️ The Leverage
- **GitHub Organizations API:** PyGithub provides robust methods for listing a user's organizations and fetching organization-specific repositories.
- **Unified Repository List UI:** Reusing the existing Dashboard repository list component with minor label adjustments.
- **Authentication Session:** Reusing the existing PAT-based session which typically carries organizational access scopes.
- **Search & Filter Patterns:** Reusing the existing search-and-filter logic applied to the `repos` route.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Lists all organizations the authenticated user belongs to.
    - `GET /api/repos?org_name=<name>`: Extends the existing repository listing route to fetch repositories from a specific organization instead of the user's personal account.
    - **Performance Optimization:** Implements a "Top 100" cap on PR/Issue aggregation via the Search API to maintain dashboard responsiveness in large enterprise environments.
- **Frontend:**
    - **Context Switcher:** A searchable dropdown in the Dashboard header to toggle between 'Personal' and discovered Organizations.
    - **Contextual Awareness:** Updating UI labels (e.g., "Repositories in [Org]") to provide clear visual feedback on the active discovery context.
    - **Session Persistence:** Remembering the last selected context during the active session.

## 🎯 The Impact
- **Enterprise Adoption:** Unlocks the ability for teams to use GH-Web as their primary interface for professional project management.
- **Reduced Context Switching:** Eliminates the need for users to manually enter organizational repository names or switch to GitHub.com to find them.
- **Strategic Positioning:** Completes the product's evolution from a niche utility tool into a comprehensive, multi-tenant repository management dashboard.

## User Stories
- **As a Professional Developer,** I want to switch my dashboard view to my company's organization so I can quickly access my daily work repositories.
- **As a Team Lead,** I want to see the PR and Issue status across all repositories in my team's organization to prioritize my reviews.
- **As a Open Source Contributor,** I want to toggle between my personal side projects and the community organizations I contribute to from a single interface.
