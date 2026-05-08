# 🌅 Horizon: Enterprise Context Switching & Organization Discovery

## 💡 The Pivot
GH-Web has successfully enabled repository discovery and management for individual users. However, the majority of professional development occurs within **GitHub Organizations**. We are pivoting to an **Enterprise-Ready Model** by introducing **Contextual Organization Discovery**. This addresses the "Organizational Blind Spot," allowing users to switch their dashboard context between their personal portfolio and the various organizations they belong to, effectively transforming GH-Web into a professional-grade management cockpit.

## ♻️ The Leverage
- **GitHub API:** PyGithub provides mature support for listing user organizations (`get_user().get_orgs()`) and organization-level repositories.
- **Unified Repository Context:** Reusing the existing `GET /api/repos` structure, extended with an optional `org_name` filter.
- **Session-Based Caching:** Reusing the authentication session to securely manage organization-specific tokens or permissions if needed.
- **UI Architecture:** Leveraging the existing tabbed interface and search bar, adding a global context switcher to the header.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Discovers and returns a list of organizations the user belongs to.
    - `GET /api/repos?org_name=<name>`: Filters repository discovery to a specific organizational context.
    - **Performance Capping:** Implementing a top-100 aggregation cap on PR and issue counts to ensure dashboard responsiveness in large enterprise environments.
- **Frontend:**
    - **Global Context Switcher:** A searchable dropdown in the application header to toggle between "Personal" and discovered Organizations.
    - **Contextual Search:** Updating the repository search to respect the active organizational context.
    - **State Management:** Persisting the selected context across tab switches (Dashboard, PRs, Issues).

## 🎯 The Impact
- **Enterprise Adoption:** Unlocks GH-Web for professional teams who work primarily within shared organizational structures.
- **Strategic Scalability:** By separating "Personal" and "Org" views, the app remains performant even as a user's total repository count grows into the hundreds or thousands.
- **Professional Credibility:** Positioning GH-Web as a tool that understands the realities of modern, collaborative software development.

## 🛡️ Error States & Edge Cases
- **Access Denied:** If a user belongs to an organization but lacks permission to list its repositories, the UI must display a "Permission Required" state with a link to GitHub organization settings.
- **Empty Organizations:** Organizations with zero repositories should show a "No Repositories Found" empty state with a "Create New Repository" CTA.
- **Secondary Rate Limiting:** Aggressive switching between large organizations may trigger GitHub's secondary rate limits. The backend must implement exponential backoff and the frontend must show a "Cooling Down" notification.
- **Mixed Visibility:** The dashboard must clearly distinguish between Internal, Private, and Public organizational repositories using existing visual badges.

## User Stories
- **As an Enterprise Developer,** I want to switch my dashboard to my company's organization so I can focus on professional PRs without the noise of my personal projects.
- **As a Team Lead,** I want to see the PR health across my organization's repositories so I can identify bottlenecks in our delivery pipeline.
- **As a Polyglot Contributor,** I want to quickly jump between my personal open-source projects and my various organizational workstreams.
