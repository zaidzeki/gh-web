# Architectural Design: Governance Phase 4 Orchestration

## 1. Overview
Governance Phase 4 extends the existing policy and metrics engine to support persistence, dynamic evaluation, and portfolio-wide aggregation.

## 2. Policy Persistence (`PolicyStore`)
The `PolicyStore` manages the lifecycle of governance rules.

- **Storage:** `app/data/policies.json` (Internal JSON storage for Phase 4).
- **Schema:**
```json
{
  "scopes": {
    "global": { "block_merge_on_critical_security": true },
    "orgs": {
      "acme-inc": { "sla_critical_hours": 24 }
    },
    "repos": {
      "acme-inc/legacy-app": { "block_merge_on_failing_ci": false }
    }
  }
}
```
- **Resolution Order:** Repository -> Organization -> Global (Most specific wins).

## 3. Governance Aggregation Service
A new service responsible for calculating the data points for the Portfolio Heatmap.

### 3.1. Data Aggregation
The service will consume:
- `PulseService`: For MTTR and Freshness metrics.
- `SecurityService`: For SLA compliance calculation.
- `PolicyService`: For current compliance status.

### 3.2. Quadrant Mapping Logic
```python
def map_to_quadrant(freshness, mttr):
    # Thresholds (Configurable)
    FRESHNESS_THRESHOLD = 80  # %
    MTTR_THRESHOLD = 24       # Hours

    if freshness >= FRESHNESS_THRESHOLD and mttr <= MTTR_THRESHOLD:
        return "Vanguard"
    if freshness < FRESHNESS_THRESHOLD and mttr <= MTTR_THRESHOLD:
        return "Artisan"
    if freshness < FRESHNESS_THRESHOLD and mttr > MTTR_THRESHOLD:
        return "Red Zone"
    return "Fragile Elite"
```

## 4. API Extensions

### 4.1. Dynamic Policy API
- `GET /api/governance/policies`: Fetch all policies (Admin only).
- `PATCH /api/repos/<full_name>/governance/policy`: Update overrides for a specific repo.

### 4.2. Heatmap API
- `GET /api/workspace/portfolio/governance/heatmap`: Returns a list of coordinate objects:
```json
[
  {
    "repo": "owner/repo",
    "x": 85,
    "y": 12,
    "quadrant": "Vanguard",
    "compliant": true
  }
]
```

## 5. Frontend Integration
- **Heatmap Component:** Uses a scatter-plot visualization.
- **Policy Editor:** A new modal component for modifying JSON-based policy overrides.
- **SLA Indicators:** Injected into the `Task Inbox` and `Repo Card` via the `health` payload.
