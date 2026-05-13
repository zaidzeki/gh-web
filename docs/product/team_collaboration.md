# PRD: Team Discovery & Contextual Collaboration

## 1. Problem Statement
The "Organization & Team Discovery" pivot successfully introduced the ability to switch between personal and organizational contexts. However, in large enterprises, a single organization can contain thousands of repositories. Even with organizational filtering, users are often overwhelmed by "noise"—repositories that belong to other departments or teams. Users need a way to further refine their context to the specific **Teams** they belong to, enabling a "Team Cockpit" view.

## 2. Objectives
- **Reduce Cognitive Load:** Allow users to filter the dashboard to only show repositories owned by or associated with a specific GitHub Team.
- **Team-Centric Task Management:** Surface PRs and Issues across all repositories associated with a team, even if the user isn't directly assigned or requested for review.
- **Seamless Context Navigation:** Integrate Team discovery into the existing Context Switcher.

## 3. User Stories
- **As a Squad Member,** I want to select my specific team (e.g., "Frontend Core") so I can see only the repos we maintain.
- **As a Team Lead,** I want to see the collective Task Inbox for my team to identify unassigned PRs or stale issues.
- **As a New Joiner,** I want to discover which teams I am a member of and instantly see the relevant codebase.

## 4. Proposed Features

### 4.1. Nested Context Switcher
- Expand the Organization dropdown to allow drilling down into "Teams" within that organization.
- Visual indicators for "Team" vs "Org" vs "Personal" contexts.

### 4.2. Team Repository Discovery
- `GET /api/user/orgs/<org>/teams`: List teams the user belongs to within an organization.
- `GET /api/repos?team_id=<id>`: Filter repositories to those associated with the specific team.

### 4.3. Team Task Inbox (V2: Team Cockpit)
- **Collective Visibility:** When a Team context is selected, the Task Inbox expands beyond the user's personal assignments to include team-wide activity.
- **Unassigned Work Discovery:** Automatically surfaces issues and PRs in team repositories that have no assignees, enabling proactive triage.
- **Peer Awareness:** Identifies tasks being handled by other team members to prevent duplicated efforts.
- **Visual Distinction:** Uses specific badges (e.g., "Team Unassigned") to distinguish collective tasks from personal ones.

## 5. Acceptance Criteria
- [x] Users can see a list of their Teams under each Organization in the switcher.
- [x] Selecting a Team context filters the Dashboard Repository list to team-owned/associated repos.
- [x] The Repository metadata (CI status, PR counts) reflects the team-filtered set.
- [x] Backend supports `GET /api/user/orgs/<org>/teams`.
- [x] Backend supports filtering `GET /api/repos` by `team_id`.
- [x] Backend `GET /api/tasks` supports `team_id` for aggregating unassigned team work.
- [x] Frontend Task Inbox displays "Unassigned" tasks when in Team context.

## 6. Technical Considerations
- **API Performance:** Team discovery might require additional API calls. Use session caching for team lists.
- **Permissions:** GitHub Team repository access levels (Read, Write, Admin) should be respected.
- **UI Complexity:** Ensure the nested dropdown remains accessible and easy to navigate on mobile/small screens.
