# Architectural Design: Phase 7 - Contextual Mission Control Engine

## 1. Overview
The Contextual Mission Control Engine evolves the aggregation services from being filesystem-dependent (scanning `/tmp/gh-web-workspaces/`) to being context-dependent (querying GitHub Organization/Team repositories).

## 2. Technical Shift

### 2.1. Dynamic Portfolio Resolution
Existing endpoints currently rely on a fixed list of active workspaces. The new architecture introduces a `resolve_effective_portfolio(org_name=None, team_id=None)` helper:

1. **Explicit Repos:** If a `repos` query parameter is provided, use it (current behavior).
2. **Workspace Fallback:** If no context is provided, use the list of active workspaces in the session's temporary directory.
3. **Context-Driven:** If `org_name` or `team_id` is provided, fetch the top 20 most recently pushed repositories from that context via the GitHub API.

### 2.2. Service Decoupling
- **Pulse Service:** Update `calculate_repo_pulse` to accept an optional `repo_obj`. If provided, it skips the expensive `get_repo` call. If the workspace directory doesn't exist, it returns `dependency_freshness_index: None` instead of failing.
- **Milestone Service:** Transition `workspace_portfolio_milestones` to use the Dynamic Portfolio Resolution. It will map milestones to repositories by querying the GitHub API for each repo in the resolved list.
- **Governance Service:** Update the heatmap aggregator to accept `org_name`.

## 3. Data Flow

1. **Frontend:** `app.js` captures `currentOrg` and `currentTeamId` from the Context Switcher.
2. **Request:** Widgets (Pulse, Roadmap, Heatmap) append these parameters to their `/api/workspace/portfolio/*` calls.
3. **Aggregation:**
    - The backend resolves the target repositories for the context.
    - `ThreadPoolExecutor` fetches data (Pulse, Milestones, Policy) for each repo.
    - Metrics are averaged/aggregated at the context level.
4. **Response:** A unified JSON response representing the "Mission Control" state for that context.

## 4. Performance & Scalability

### 4.1. Aggressive Caching
Aggregation for an entire Organization can be expensive.
- **Cache Key:** `(github_token, context_type, context_id)`.
- **TTL:** 1 hour for strategic metrics.
- **Bypass:** A "Refresh" button on the UI will explicitly clear the cache for that context.

### 4.2. Resource Limits
- **Repo Cap:** Aggregation is capped at 20 repositories per context to stay within GitHub API rate limits and ensure sub-5s response times.
- **Parallelism:** Max 10 concurrent threads for API fetching.

## 5. Security
- **Context Validation:** The engine must verify that the user has at least `read` access to the requested Organization or Team before performing aggregation.
- **Permission Mapping:** `evaluate_repo_policy` already respects per-repo permissions; this behavior is maintained.
