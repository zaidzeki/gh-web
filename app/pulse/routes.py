import datetime
import statistics
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, session, jsonify
from github import Github, Auth
from ..workspace.utils import mask_token

bp = Blueprint('pulse', __name__)

# Simple in-memory cache: { (token, repo_full_name): (timestamp, data) }
_pulse_cache = {}
CACHE_TTL = datetime.timedelta(minutes=60)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    auth = Auth.Token(token)
    return Github(auth=auth, timeout=30)

def get_production_environment(repo):
    try:
        envs = repo.get_environments()
        synonyms = ['production', 'prod', 'live']
        for env in envs:
            if env.name.lower() in synonyms:
                return env.name
        # Fallback to first env if any
        for env in envs:
            return env.name
    except:
        pass
    return None

def _get_window_metrics(g, repo, prod_env, start_date, end_date):
    """Calculates DORA metrics for a specific time window."""
    # 1. Fetch Deployments
    deployments = repo.get_deployments(environment=prod_env)
    prod_deployments = []

    # We may need to look slightly before start_date to find a failure that was restored within the window,
    # OR look slightly after end_date to find a success that restored a failure within the window.
    # For simplicity and performance, we focus on deployments CREATED within the window.
    for i, d in enumerate(deployments):
        if i >= 100: break # Increased limit for dual window scan

        d_created_at = d.created_at.replace(tzinfo=datetime.timezone.utc)
        if d_created_at < start_date:
            continue
        if d_created_at > end_date:
            continue

        statuses = d.get_statuses()
        latest_status = None
        for s in statuses:
            latest_status = str(s.state)
            break

        prod_deployments.append({
            "id": d.id,
            "sha": str(d.sha),
            "created_at": d_created_at,
            "status": latest_status
        })

    # Sort deployments by creation time ascending
    prod_deployments.sort(key=lambda x: x["created_at"])

    # 2. Deployment Frequency (Successful production deployments in window)
    successful_deployments = [d for d in prod_deployments if d["status"] == "success"]
    deployment_frequency = len(successful_deployments)

    # 3. Change Failure Rate (% of production deployments in window that failed)
    total_deployments = len(prod_deployments)
    failure_deployments = [d for d in prod_deployments if d["status"] == "failure"]
    change_failure_rate = (len(failure_deployments) / total_deployments * 100) if total_deployments > 0 else 0.0

    # 4. Time to Restore (Median time from failure to next success within window)
    restore_times = []
    for i, d in enumerate(prod_deployments):
        if d["status"] == "failure":
            # Find the next successful deployment
            for next_d in prod_deployments[i+1:]:
                if next_d["status"] == "success":
                    delta = next_d["created_at"] - d["created_at"]
                    restore_times.append(delta.total_seconds() / 3600)
                    break

    time_to_restore = statistics.median(restore_times) if restore_times else None

    # 5. Lead Time to Change (Median time from PR merge to production deployment within window)
    # Fetch PRs merged in the window
    query = f"repo:{repo.full_name} is:pr is:merged merged:{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}..{end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    merged_prs = g.search_issues(query)

    lead_times = []
    for i, pr_issue in enumerate(merged_prs):
        if i >= 50: break

        pr = repo.get_pull(pr_issue.number)
        if not pr.merged_at: continue

        merged_at = pr.merged_at.replace(tzinfo=datetime.timezone.utc)

        # Find earliest successful deployment created after merge_at (even if deployment is outside window,
        # but here we use successful_deployments from this window for consistency)
        earliest_deploy = None
        for d in successful_deployments:
            if d["created_at"] > merged_at:
                if earliest_deploy is None or d["created_at"] < earliest_deploy["created_at"]:
                    earliest_deploy = d

        if earliest_deploy:
            delta = earliest_deploy["created_at"] - merged_at
            lead_times.append(delta.total_seconds() / 3600)

    lead_time_to_change = statistics.median(lead_times) if lead_times else None

    return {
        "deployment_frequency": deployment_frequency,
        "lead_time_to_change_hours": round(lead_time_to_change, 2) if lead_time_to_change is not None else None,
        "change_failure_rate_percent": round(change_failure_rate, 2),
        "time_to_restore_hours": round(time_to_restore, 2) if time_to_restore is not None else None
    }

def _calculate_trends(current, previous):
    """Compares current vs previous metrics to determine trends."""
    trends = {}

    def get_trend(curr, prev, higher_is_better=True):
        if curr is None or prev is None:
            return "stable"
        if curr == prev:
            return "stable"

        improving = curr > prev if higher_is_better else curr < prev
        return "improving" if improving else "degrading"

    trends["deployment_frequency"] = get_trend(current["deployment_frequency"], previous["deployment_frequency"], True)
    trends["lead_time_to_change_hours"] = get_trend(current["lead_time_to_change_hours"], previous["lead_time_to_change_hours"], False)
    trends["change_failure_rate_percent"] = get_trend(current["change_failure_rate_percent"], previous["change_failure_rate_percent"], False)
    trends["time_to_restore_hours"] = get_trend(current["time_to_restore_hours"], previous["time_to_restore_hours"], False)

    return trends

def _classify_tier(metrics):
    """Classifies repository performance into DORA tiers."""
    tiers = {
        "Elite": 4,
        "High": 3,
        "Medium": 2,
        "Low": 1
    }
    reverse_tiers = {v: k for k, v in tiers.items()}

    def get_df_tier(v):
        if v > 30: return "Elite"
        if v >= 4: return "High"
        if v >= 1: return "Medium"
        return "Low"

    def get_lt_tier(v):
        if v is None: return "Low"
        if v < 24: return "Elite"
        if v < 168: return "High"
        if v < 720: return "Medium"
        return "Low"

    def get_cfr_tier(v):
        if v < 15: return "Elite"
        if v <= 30: return "High"
        if v <= 45: return "Medium"
        return "Low"

    def get_restore_tier(v):
        if v is None: return "Elite"
        if v < 1: return "Elite"
        if v < 24: return "High"
        if v < 168: return "Medium"
        return "Low"

    metric_tiers = {
        "deployment_frequency": get_df_tier(metrics["deployment_frequency"]),
        "lead_time_to_change_hours": get_lt_tier(metrics["lead_time_to_change_hours"]),
        "change_failure_rate_percent": get_cfr_tier(metrics["change_failure_rate_percent"]),
        "time_to_restore_hours": get_restore_tier(metrics["time_to_restore_hours"])
    }

    # Overall tier is the average (rounded down) of metric tiers
    avg_score = sum(tiers[t] for t in metric_tiers.values()) / 4
    overall_tier = reverse_tiers[int(avg_score)]

    return {
        "overall": overall_tier,
        "metrics": metric_tiers
    }

def calculate_repo_pulse(g, repo_full_name):
    try:
        repo = g.get_repo(repo_full_name)
        prod_env = get_production_environment(repo)

        if not prod_env:
            return {
                "repo": repo_full_name,
                "metrics": {
                    "deployment_frequency": 0,
                    "lead_time_to_change_hours": None,
                    "change_failure_rate_percent": 0.0,
                    "time_to_restore_hours": None
                },
                "info": "No production environment found"
            }

        now = datetime.datetime.now(datetime.timezone.utc)
        thirty_days_ago = now - datetime.timedelta(days=30)
        sixty_days_ago = now - datetime.timedelta(days=60)

        current_metrics = _get_window_metrics(g, repo, prod_env, thirty_days_ago, now)
        previous_metrics = _get_window_metrics(g, repo, prod_env, sixty_days_ago, thirty_days_ago)

        trends = _calculate_trends(current_metrics, previous_metrics)
        benchmarks = _classify_tier(current_metrics)

        return {
            "repo": repo_full_name,
            "window_days": 30,
            "metrics": current_metrics,
            "previous_metrics": previous_metrics,
            "trends": trends,
            "benchmarks": benchmarks
        }
    except Exception as e:
        return {"error": mask_token(str(e))}

@bp.route('/api/repos/<path:full_name>/pulse', methods=['GET'])
def get_repo_pulse(full_name):
    token = session.get('github_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    # Simple Caching
    cache_key = (token, full_name)
    now = datetime.datetime.now()
    if cache_key in _pulse_cache:
        timestamp, data = _pulse_cache[cache_key]
        if now - timestamp < CACHE_TTL:
            return jsonify(data), 200

    g = get_github_client()
    result = calculate_repo_pulse(g, full_name)

    if "error" in result:
        return jsonify(result), 500

    _pulse_cache[cache_key] = (now, result)
    return jsonify(result), 200

@bp.route('/api/workspace/portfolio/pulse', methods=['GET'])
def get_portfolio_pulse():
    token = session.get('github_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    repo_names = request.args.get('repos', '').split(',')
    repo_names = [r.strip() for r in repo_names if r.strip()]

    if not repo_names:
        return jsonify({
            "metrics": {
                "deployment_frequency": 0,
                "lead_time_to_change_hours": None,
                "change_failure_rate_percent": 0.0,
                "time_to_restore_hours": None
            }
        }), 200

    # Security Enhancement: Limit the number of repositories to process
    if len(repo_names) > 50:
        return jsonify({"error": "Too many repositories requested (max 50)"}), 400

    for name in repo_names:
        if len(name) > 255:
            return jsonify({"error": f"Repository name too long: {name[:50]}..."}), 400

    g = get_github_client()
    now = datetime.datetime.now()

    def fetch_and_cache(full_name):
        cache_key = (token, full_name)
        if cache_key in _pulse_cache:
            timestamp, data = _pulse_cache[cache_key]
            if now - timestamp < CACHE_TTL:
                return data

        data = calculate_repo_pulse(g, full_name)
        if "error" not in data:
            _pulse_cache[cache_key] = (now, data)
        return data

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_and_cache, name) for name in repo_names]
        for future in futures:
            results.append(future.result())

    # Aggregate Metrics
    agg = {
        "deployment_frequency": 0,
        "lead_time_to_change_hours": [],
        "change_failure_rate_percent": [],
        "time_to_restore_hours": []
    }
    prev_agg = {
        "deployment_frequency": 0,
        "lead_time_to_change_hours": [],
        "change_failure_rate_percent": [],
        "time_to_restore_hours": []
    }

    valid_repos = 0
    for res in results:
        if "error" in res or "metrics" not in res:
            continue

        valid_repos += 1
        m = res["metrics"]
        agg["deployment_frequency"] += m["deployment_frequency"]
        if m["lead_time_to_change_hours"] is not None:
            agg["lead_time_to_change_hours"].append(m["lead_time_to_change_hours"])
        agg["change_failure_rate_percent"].append(m["change_failure_rate_percent"])
        if m["time_to_restore_hours"] is not None:
            agg["time_to_restore_hours"].append(m["time_to_restore_hours"])

        pm = res.get("previous_metrics")
        if pm:
            prev_agg["deployment_frequency"] += pm["deployment_frequency"]
            if pm["lead_time_to_change_hours"] is not None:
                prev_agg["lead_time_to_change_hours"].append(pm["lead_time_to_change_hours"])
            prev_agg["change_failure_rate_percent"].append(pm["change_failure_rate_percent"])
            if pm["time_to_restore_hours"] is not None:
                prev_agg["time_to_restore_hours"].append(pm["time_to_restore_hours"])

    summary = {
        "deployment_frequency": agg["deployment_frequency"],
        "lead_time_to_change_hours": round(statistics.mean(agg["lead_time_to_change_hours"]), 2) if agg["lead_time_to_change_hours"] else None,
        "change_failure_rate_percent": round(statistics.mean(agg["change_failure_rate_percent"]), 2) if agg["change_failure_rate_percent"] else 0.0,
        "time_to_restore_hours": round(statistics.mean(agg["time_to_restore_hours"]), 2) if agg["time_to_restore_hours"] else None,
        "repo_count": valid_repos
    }

    prev_summary = {
        "deployment_frequency": prev_agg["deployment_frequency"],
        "lead_time_to_change_hours": round(statistics.mean(prev_agg["lead_time_to_change_hours"]), 2) if prev_agg["lead_time_to_change_hours"] else None,
        "change_failure_rate_percent": round(statistics.mean(prev_agg["change_failure_rate_percent"]), 2) if prev_agg["change_failure_rate_percent"] else 0.0,
        "time_to_restore_hours": round(statistics.mean(prev_agg["time_to_restore_hours"]), 2) if prev_agg["time_to_restore_hours"] else None
    }

    trends = _calculate_trends(summary, prev_summary)
    benchmarks = _classify_tier(summary)

    return jsonify({
        "metrics": summary,
        "previous_metrics": prev_summary,
        "trends": trends,
        "benchmarks": benchmarks,
        "repos": results
    }), 200
