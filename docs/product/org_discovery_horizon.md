# 🌅 Horizon: Organization & Team Discovery Expansion Proposal

## 💡 The Pivot
GH-Web currently operates as a personal productivity tool, focusing on repositories owned by or directly assigned to the authenticated user. We are pivoting to an **Enterprise-Ready Portfolio Hub**. By introducing **Organization Discovery** and a **Contextual Dashboard**, we allow users to seamlessly switch between their personal work and their professional responsibilities within GitHub Organizations. This transforms GH-Web from a "solo dev tool" into a "team-aware management cockpit."

## ♻️ The Leverage
- **Authentication:** Reuses the existing GitHub PAT session and authenticated client.
- **Repository Discovery UI:** Reuses the searchable repository list and action patterns.
- **GitHub Orgs API:** PyGithub already provides full support for organization and team membership discovery.
- **Session Management:** Leveraging the Flask session to cache organization lists for performance, as per product standards.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Fetches and caches the list of organizations the user belongs to.
    - `GET /api/repos`: Enhanced to support an `org_name` parameter for contextual repository listing.
    - **Scalability Optimization:** Capping PR/Issue metadata aggregation at the top 100 items for organization contexts to maintain responsiveness.
- **Frontend:**
    - **Context Switcher:** A new dropdown in the header (next to the user profile) to toggle between "Personal" and discovered Organizations.
    - **Stateful Navigation:** Switching context automatically refreshes the Dashboard repository list and Task Inbox (where applicable).

## 🎯 The Impact
- **Enterprise Adoption:** Organizations can now use GH-Web as a unified interface for their entire engineering portfolio.
- **Discovery Velocity:** Users can explore repositories they have access to but don't "own," reducing the barrier to cross-team collaboration.
- **Product Stickiness:** By handling both personal and professional contexts, GH-Web becomes the primary daily entry point for all GitHub-related tasks.
