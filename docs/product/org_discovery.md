# PRD: Organization & Team Discovery

## 1. Problem Statement
GH-Web's repository discovery is currently limited to the authenticated user's personal repositories. This creates an "Organizational Blind Spot" for enterprise developers who spend the majority of their time working on repositories owned by GitHub Organizations. Users are forced to revert to manual entry for organizational repos, breaking the "Dashboard-First" UX.

## 2. Objectives
- **Enterprise Enablement:** Allow users to discover and manage repositories within their GitHub Organizations.
- **Seamless Context Switching:** Provide a low-friction way to toggle between personal and organizational work.
- **Performance at Scale:** Ensure that repository listing and metadata aggregation (PR/Issue counts) remain fast even in large organizations.
- **Consistency:** Maintain a unified UI experience across different context views.

## 3. User Stories
- **As a Developer,** I want to see a list of my GitHub Organizations so that I can select the context I'm currently working in.
- **As a Member of a Large Org,** I want the repository dashboard to load quickly even if the organization has hundreds of repositories.
- **As a Multi-Tasker,** I want the Task Inbox and PR list to update automatically when I switch organization context.
- **As a Power User,** I want to search for specific repositories within an organization's portfolio.

## 4. Proposed Features

### 4.1. Context Switcher Component
- **UI:** A searchable dropdown in the application header (near the user profile).
- **Options:** "Personal" (default) followed by a list of all discovered Organizations.
- **Behavior:** Selecting an organization updates the global state and triggers a refresh of the Dashboard, Tasks, and Repositories tabs.

### 4.2. Organization Discovery API
- **Endpoint:** `GET /api/user/orgs`
- **Behavior:** Fetches the list of organizations the authenticated user belongs to.
- **Caching:** Stores the list in the Flask session to reduce API calls and improve responsiveness.

### 4.3. Enhanced Repository API
- **Endpoint:** `GET /api/repos?org_name=<name>`
- **Logic Update:**
    - If `org_name` is provided, fetch repositories for that organization.
    - Aggregate PR and Issue counts using the Search API, scoped to the selected organization.
    - **Scalability Constraint:** Limit aggregation to the top 100 most recently updated items to prevent timeouts.

### 4.4. Dashboard Integration
- **UI:** The Dashboard repository list and Task Inbox will respect the active organization filter.
- **Visual Cues:** Display the active context name prominently on the Dashboard.

## 5. Acceptance Criteria
- [ ] Users can see a list of their organizations in a dropdown switcher.
- [ ] Switching the context to an organization correctly lists its repositories in the Dashboard.
- [ ] PR and Issue counts are accurately displayed for organizational repositories.
- [ ] The application remembers the selected context during the session.
- [ ] API performance remains under 2 seconds for organizations with up to 100 repositories.

## 6. Success Metrics
- **Context Switch Latency:** Time taken to refresh the dashboard after switching context.
- **Organizational Engagement:** Percentage of users who utilize the context switcher.
- **Discovery Coverage:** Ratio of organizational repos managed via GH-Web vs. manual entry.
