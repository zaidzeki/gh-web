# 🌅 Horizon: Organization & Team Discovery

## 💡 The Pivot
GH-Web has successfully transitioned to a Dashboard-First UX for individual developers. However, professional development often happens within the context of **GitHub Organizations**. We are pivoting to an **Enterprise-Ready Discovery Model**. By surfacing organizations and teams directly within the dashboard, we bridge the "Organizational Blind Spot," allowing users to switch contexts and manage professional projects with the same fluidity as their personal repositories.

## ♻️ The Leverage
- **Authentication System:** Reuses the existing GitHub PAT session and permission model.
- **Repository Metadata Engine:** Reuses the PR/Issue count aggregation logic developed for personal repositories.
- **Dashboard Infrastructure:** Extends the searchable repository list and portfolio monitoring to support organizational contexts.
- **Task Inbox:** Leveraging the existing task aggregation to filter by organization-specific assignments and review requests.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Discovers and returns a list of organizations the user belongs to.
    - Updated `GET /api/repos`: Support for `org_name` filtering to fetch repositories within a specific organization context.
    - **Performance Optimization:** Implements session-based caching for organization lists and metadata aggregation caps (top 100 items) to handle large enterprise environments.
- **Frontend:**
    - **Context Switcher:** A new dropdown in the Dashboard header to toggle between "Personal" and discovered Organizations.
    - **Contextual Filtering:** Automatic updates to the Task Inbox and Workspace Portfolio when a new organization context is selected.

## 🎯 The Impact
- **Enterprise Utility:** Unlocks the bulk of a professional developer's daily work, increasing DAU and product stickiness.
- **Scalable Discovery:** Provides a structured path to navigate thousands of repositories without overwhelming the user.
- **Strategic Position:** Positions GH-Web as the definitive interface for both independent contributors and enterprise teams.

## User Stories
- **As an Enterprise Developer,** I want to switch my dashboard context to my company's organization so I can quickly find internal projects.
- **As a Team Lead,** I want to see a filtered view of active PRs within my organization's repositories to identify blockers.
- **As a Consultant,** I want to toggle between different client organizations without needing to re-authenticate or re-login.
