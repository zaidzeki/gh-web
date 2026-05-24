# Architectural Design: Project Pulse Metrics Engine

## 1. Overview
The "Project Pulse" engine is responsible for aggregating and calculating DORA metrics (Deployment Frequency, Lead Time, Change Failure Rate, Time to Restore) by analyzing GitHub repository events. It acts as a higher-level analytical layer on top of the existing `repos` and `deployments` blueprints.

## 2. Metric Definitions & Calculation Logic

### 2.1. Deployment Frequency
- **Source:** `GET /repos/{owner}/{repo}/deployments`
- **Calculation:** Count of deployments to the 'production' environment with a `success` status within the last 30 days.
- **Goal:** Higher frequency indicates higher delivery velocity and smaller, lower-risk batches.

### 2.2. Lead Time to Change
- **Source:** `GET /repos/{owner}/{repo}/pulls` (merged) and `GET /repos/{owner}/{repo}/deployments`
- **Calculation:**
    1. Identify all PRs merged in the last 30 days.
    2. For each merged PR, find the earliest successful production deployment that contains the PR's `merge_commit_sha`.
    3. Lead Time = `deployment.created_at - pr.merged_at`.
    4. Metric = Median of all calculated lead times.
- **Goal:** Lower lead time indicates an efficient review and deployment pipeline.

### 2.3. Change Failure Rate
- **Source:** `GET /repos/{owner}/{repo}/deployments` and their statuses.
- **Calculation:** `(Count of deployments with 'failure' status) / (Total count of deployments)` to the production environment in the last 30 days.
- **Goal:** Lower rate indicates higher deployment stability.

### 2.4. Time to Restore Service
- **Source:** `GET /repos/{owner}/{repo}/deployments` statuses.
- **Calculation:**
    1. Identify production deployments that resulted in a `failure`.
    2. For each failure, find the next production deployment that resulted in a `success`.
    3. Restore Time = `success_deployment.created_at - failure_deployment.created_at`.
    4. Metric = Median of all restore times.
- **Goal:** Lower time indicates better incident response and recovery capabilities.

## 3. API Design

### 3.1. Repository Pulse
- **Endpoint:** `GET /api/repos/<full_name>/pulse`
- **Response:**
```json
{
  "repo": "owner/repo",
  "window_days": 30,
  "metrics": {
    "deployment_frequency": 12,
    "lead_time_to_change_hours": 4.5,
    "change_failure_rate_percent": 8.3,
    "time_to_restore_hours": 1.2
  },
  "trends": {
    "deployment_frequency": "up",
    "lead_time_to_change": "down"
  }
}
```

### 3.2. Portfolio Pulse Aggregation
- **Endpoint:** `GET /api/workspace/portfolio/pulse`
- **Logic:** Uses `ThreadPoolExecutor` to fetch and average the metrics across all repositories in the active workspace context (matching the `workspace_portfolio` repo list).

## 4. Performance & Scalability
- **Parallelization:** Like the `repos/health` endpoint, the Pulse engine will use `ThreadPoolExecutor` to fetch PR and Deployment data in parallel.
- **Scan Depth:** To maintain performance, the engine will limit its historical scan to the last 100 PRs and 100 deployments per repository.
- **Caching:** Calculated metrics will be cached in the Flask application (or session) with a TTL of 60 minutes to prevent redundant expensive calculations during dashboard refreshes.

## 5. Security
- **Access Control:** The engine respects the user's GitHub PAT permissions; metrics are only calculated for repositories the user can read.
- **Token Masking:** All error messages from the GitHub API will be passed through the `mask_token` utility.
