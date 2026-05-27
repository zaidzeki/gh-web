# Architectural Design: Security Integration & Vulnerability Monitoring

## 1. Overview
The Security Integration extends the GH-Web monitoring engine to include GitHub's Security Advisories and Alerts. It follows the existing pattern of parallelized API aggregation and backend normalization to provide a unified "Security Health" score for repositories.

## 2. API Extensions

### 2.1. Security Alert Aggregation
- **Endpoint:** `GET /api/repos/<full_name>/security/alerts`
- **Responsibility:** Aggregates alerts from three primary GitHub sources:
    - **Dependabot Alerts:** `GET /repos/{owner}/{repo}/dependabot/alerts`
    - **Secret Scanning Alerts:** `GET /repos/{owner}/{repo}/secret-scanning/alerts`
    - **Code Scanning Alerts:** `GET /repos/{owner}/{repo}/code-scanning/alerts`
- **Data Structure (Normalized):**
```json
{
  "summary": {
    "vulnerabilities": {"critical": 2, "high": 5, "medium": 10, "low": 0},
    "secrets": {"open": 1},
    "code_scanning": {"errors": 3, "warnings": 12}
  },
  "alerts": [
    {
      "type": "dependabot",
      "severity": "critical",
      "package": "django",
      "fixed_in": "4.2.1",
      "html_url": "..."
    }
  ]
}
```

### 2.2. Task Normalization (`app/tasks/routes.py`)
- The `normalize` function will be updated to include security alerts as a new `category`: `security_vulnerability`.
- Security tasks will be prioritized in the Unified Task Inbox alongside `review_requested` and `assigned` tasks.

### 2.3. Dashboard Enrichment (`app/repos/routes.py`)
- The `get_repos_health` endpoint will be updated to include a `security_status` field.
- **Security Score Calculation:**
    - `failure`: If any 'critical' or 'high' vulnerabilities exist, or any open secrets are detected.
    - `warning`: If 'medium' or 'low' vulnerabilities exist.
    - `success`: No security alerts.

## 3. Frontend Integration

### 3.1. Dashboard Badges
- A new `🛡️` icon will be added to Repository Cards.
- The color of the shield reflects the `security_status`.
- Tooltip displays the breakdown (e.g., "2 Critical, 5 High").

### 3.2. Security Dashboard Component
- A new section in the Portfolio view showing the "Top 5 Most Vulnerable Repositories".
- Aggregated shield indicator for the entire portfolio.

## 4. Technical Constraints & Security
- **API Scope Requirements:** PATs must have `security_events` and `repo` scopes. The backend will return a specific `403 Forbidden` error with an informative message if these scopes are missing.
- **Fail-Safe Processing:** Since security APIs may be disabled for private repositories on certain plans, the `fetch_repo_health` function must handle `404` or `403` from security endpoints without crashing the entire health check.
- **Throttling:** Security alert fetching will be included in the `ThreadPoolExecutor` and subject to the same batch limits (50 repos) and caching TTL (60 mins) as Pulse metrics.
