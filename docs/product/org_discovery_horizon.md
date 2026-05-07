# 🌅 Horizon: Organization & Team Discovery Expansion Proposal

## 💡 The Pivot
GH-Web has successfully transitioned from manual entry to a personal "Control Center" through repository discovery. However, most professional development occurs within **GitHub Organizations**. We are pivoting from a "Personal Portfolio Tool" to an **Enterprise-Ready Repository Dashboard**. By adding Organization and Team discovery, we bridge the "Organizational Blind Spot," enabling users to manage professional projects with the same ease as their personal repositories.

## ♻️ The Leverage
This expansion maximizes ROI by reusing:
- **Core Discovery Engine:** Reuses the repository listing, sorting, and metadata enrichment logic.
- **Search API Integration:** Leverages existing patterns for aggregated PR and Issue counts.
- **Contextual UI:** Extends the Dashboard list-group and filtering patterns to handle organization context.
- **Session-Based Auth:** Reuses the existing GitHub PAT for organization-level permissions.

## 🚀 The Delta
- **Backend:**
    - `GET /api/user/orgs`: Lists organizations the user belongs to.
    - Enhanced `GET /api/repos`: Added `org_name` parameter to fetch repositories within a specific organization context.
    - Context-Aware Aggregation: Updated metadata fetching to filter Issues and PRs based on the selected organization.
- **Frontend:**
    - **Context Switcher:** A new dropdown in the Dashboard header to toggle between 'Personal' and various 'Organization' views.
    - **Seamless Reload:** Real-time updates of the repository list when the discovery context changes.
    - **Team Awareness:** (Future) Expanding to support specific Team-based filtering within Organizations.

## 🎯 The Impact
- **Unlocks Enterprise Value:** Positions GH-Web as a tool for "Real Work," increasing its footprint in professional settings.
- **Unified Workspace:** Provides a single interface for managing all GitHub work, regardless of ownership.
- **Scalability:** Handles users with hundreds of repositories across multiple contexts without discovery fatigue.
