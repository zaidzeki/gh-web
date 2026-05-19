# Architecture: Milestone Integration & Goal Tracking

## 1. Overview
The Milestone Integration expands the GH-Web data model to include the `Milestone` entity. This layer sits above Issues and PRs, providing a grouping mechanism for goal-oriented task management.

## 2. API Extensions

### 2.1. Milestone Discovery (`repos` or new `milestones` blueprint)
- `GET /api/repos/<full_name>/milestones`: Returns a list of milestones.
  - **Data Structure:**
    ```json
    {
      "id": 123,
      "number": 1,
      "title": "v1.0 Release",
      "description": "Initial stable release",
      "state": "open",
      "open_issues": 5,
      "closed_issues": 10,
      "due_on": "2025-12-31T00:00:00Z",
      "progress": 66.6
    }
    ```
- `POST /api/repos/<full_name>/milestones`: Creates a milestone.
  - **Parameters:** `title`, `description` (opt), `due_on` (opt), `state` (open/closed).

### 2.2. Task Assignment (`issues` blueprint)
- `POST /api/repos/<full_name>/issues/<number>/milestone`: Updates the milestone associated with an issue or PR.
  - **Parameters:** `milestone_number` (int or null to clear).

## 3. Frontend Integration

### 3.1. Navigation
- A new **Milestones** tab will be added to the main navigation (adjacent to Issues and PRs).

### 3.2. Dashboard Enrichment
- The `GET /api/repos` response will be enriched with a `next_milestone` object containing the title and due date of the soonest open milestone.

### 3.3. Task Inbox Filtering
- The `GET /api/tasks` endpoint will accept an optional `milestone_number` parameter to filter the inbox.
- UI: A milestone filter dropdown will be added to the Unified Task Inbox header.

### 3.4. Portfolio Roadmap Visualization
- A new **Portfolio Roadmap** component on the Dashboard.
- Data Source: `GET /api/workspace/portfolio/milestones`.
- Visualization: A vertical timeline of milestones from all active workspaces, sorted by `due_on` ASC.

## 4. Technical Considerations

### 4.1. Portfolio Aggregation
- The backend will scan the `workspace/portfolio` and perform parallel fetches (similar to `repos/health`) for milestones.
- To prevent performance degradation, the aggregation will be capped at the first 10 repositories in the portfolio.

### 4.2. Calculations
- **Progress:** Backend will calculate `(closed / (open + closed)) * 100` to provide a ready-to-render percentage for the progress bars.

### 4.3. Performance
- Milestone counts are typically low (<50 per repo), so N+1 is not a major concern. However, they should be included in the initial repository metadata fetch if possible to avoid secondary roundtrips on the dashboard.

### 4.4. Security
- Standard `mask_token` and `secure_filename` (for repo names) will be applied.
- All operations require an authenticated GitHub PAT in the session.
