# Architecture: Task Orchestration Engine

## 1. Overview
The **Task Orchestration Engine** is a backend component responsible for aggregating actionable items from across the user's GitHub portfolio. It abstracts the complexity of multiple GitHub API calls into a single, normalized "Task" stream.

## 2. Data Flow
1. **Request:** Frontend calls `GET /api/tasks`.
2. **Aggregation:** The engine executes three concurrent (or sequential, depending on rate limits) searches via `PyGithub`:
    - `is:pr is:open review-requested:{user}` (Action Required)
    - `is:issue is:open assignee:{user}` (In Progress)
    - `is:pr is:open author:{user}` (My Pull Requests)
3. **Normalization:** Results are mapped to a common `Task` schema.
4. **Enrichment:** For owned PRs, the engine fetches the combined CI status (Success/Failure/Pending).
5. **Response:** A JSON array of tasks categorized by priority.

## 3. Normalized Task Schema
```json
{
  "id": "repo_full_name#number",
  "type": "issue | pr",
  "category": "review_requested | assigned | authored",
  "title": "Fix the flux capacitor",
  "repo": "owner/repo",
  "number": 42,
  "html_url": "...",
  "updated_at": "2025-05-30T...",
  "ci_status": "success | failure | pending | null",
  "review_status": "approved | changes_requested | pending | null"
}
```

## 4. Components
- **`app/tasks/routes.py`:** Implements the API endpoints.
- **GitHub Search API:** Leveraged for efficient cross-repository discovery.
- **Task Orchestrator:** A utility class/function to handle the aggregation logic.

## 5. Scalability & Performance
- **Caching:** Initial implementation will rely on live fetches. Future iterations may cache results for 60 seconds to avoid GitHub secondary rate limits.
- **Batching:** Uses `g.search_issues` to fetch up to 30 items per category in a single request.
