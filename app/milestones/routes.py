import os
from flask import Blueprint, request, session, jsonify
import github
from github import Github
import git
import datetime
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from ..workspace.utils import (
    mask_token, get_repo_full_name_from_url, resolve_effective_portfolio
)
from ..pulse.routes import calculate_repo_pulse

bp = Blueprint('milestones', __name__)

# Context-level cache: { (token, context_key): (timestamp, data) }
_portfolio_milestones_cache = {}
CACHE_TTL = datetime.timedelta(minutes=60)

def calculate_certainty(open_issues, lead_time_hours, due_on):
    """
    Calculates the Delivery Certainty Score.
    Certainty = Time Remaining / (Remaining Work * Velocity)
    """
    if not due_on:
        return {"score": None, "tier": "Unknown", "message": "No deadline set"}

    if open_issues == 0:
        return {"score": 2.0, "tier": "High", "message": "All tasks completed"}

    # Use a default velocity of 48h if no historical lead time is available
    velocity = lead_time_hours if lead_time_hours is not None else 48.0
    time_needed = open_issues * velocity

    now = datetime.datetime.now(datetime.timezone.utc)
    if due_on.tzinfo is None:
        due_on = due_on.replace(tzinfo=datetime.timezone.utc)

    time_remaining_td = due_on - now
    time_remaining_hours = time_remaining_td.total_seconds() / 3600

    if time_remaining_hours <= 0:
        return {"score": 0.0, "tier": "Low", "message": "Deadline passed"}

    certainty = time_remaining_hours / time_needed

    tier = "Low"
    if certainty > 1.2:
        tier = "High"
    elif certainty >= 0.9:
        tier = "Medium"

    return {
        "score": round(certainty, 2),
        "tier": tier,
        "message": f"Predicted to finish {'ahead of' if certainty > 1 else 'behind'} schedule"
    }

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    # Security Enhancement: Add timeout to prevent resource exhaustion from hanging API calls
    return Github(auth=github.Auth.Token(token), timeout=30)

@bp.route('/api/repos/<path:full_name>/milestones', methods=['GET'])
def list_milestones(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    state = request.args.get('state', 'open')

    # Security Enhancement: Whitelist state parameter
    if state not in ['open', 'closed', 'all']:
        return jsonify({"error": "Invalid state parameter"}), 400

    try:
        repo = g.get_repo(full_name)
        milestones = repo.get_milestones(state=state)
        # Security Enhancement: Limit to first 100 items to prevent DoS/resource exhaustion
        results = []
        for i, ms in enumerate(milestones):
            if i >= 100: break
            results.append({
                "number": int(ms.number),
                "title": str(ms.title),
                "description": str(ms.description) if ms.description else "",
                "state": str(ms.state),
                "open_issues": int(ms.open_issues),
                "closed_issues": int(ms.closed_issues),
                "due_on": ms.due_on.isoformat() if ms.due_on else None,
                "html_url": str(ms.html_url)
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/repos/<path:full_name>/milestones', methods=['POST'])
def create_milestone(full_name):
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    title = data.get('title')
    description = data.get('description', '')
    due_on = data.get('due_on') # Expected in ISO format if provided

    if not title:
        return jsonify({"error": "Milestone title is required"}), 400

    # Security Enhancement: Input length validation
    if len(title) > 256:
        return jsonify({"error": "Title is too long (max 256 characters)"}), 400
    if description and len(description) > 1024:
        return jsonify({"error": "Description is too long (max 1024 characters)"}), 400

    try:
        repo = g.get_repo(full_name)
        params = {"title": title, "description": description}
        if due_on:
            import datetime
            try:
                params["due_on"] = datetime.datetime.fromisoformat(due_on.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid due_on format. Expected ISO 8601."}), 400

        ms = repo.create_milestone(**params)
        return jsonify({
            "message": "Milestone created successfully",
            "number": ms.number,
            "title": ms.title
        }), 201
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500

@bp.route('/api/workspace/portfolio/milestones', methods=['GET'])
def workspace_portfolio_milestones():
    token = session.get('github_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    org_name = request.args.get('org_name')
    team_id = request.args.get('team_id')
    repos_arg = request.args.get('repos')
    force_refresh = request.args.get('force_refresh') in ['true', '1']

    # Context Caching
    context_key = f"{org_name}:{team_id}:{repos_arg}"
    cache_key = (token, context_key)
    now_ts = datetime.datetime.now()

    if not force_refresh and cache_key in _portfolio_milestones_cache:
        timestamp, data = _portfolio_milestones_cache[cache_key]
        if now_ts - timestamp < CACHE_TTL:
            return jsonify(data), 200

    g = get_github_client()
    repo_names = resolve_effective_portfolio(g, org_name, team_id, repos_arg)

    if not repo_names:
        return jsonify([]), 200

    def fetch_repo_milestones(full_name):
        try:
            g_local = Github(auth=github.Auth.Token(token), timeout=30)
            gh_repo = g_local.get_repo(full_name)
            milestones = gh_repo.get_milestones(state='open')

            # Fetch Pulse for Lead Time
            pulse = calculate_repo_pulse(g, full_name, repo_obj=gh_repo)
            lead_time = pulse.get("metrics", {}).get("lead_time_to_change_hours")

            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)

            repo_milestones = []
            for ms in milestones:
                total = int(ms.open_issues) + int(ms.closed_issues)
                progress = (int(ms.closed_issues) / total * 100) if total > 0 else 0
                is_overdue = False
                due = ms.due_on
                if ms.due_on:
                    # ms.due_on is often naive but usually UTC from PyGithub
                    if due.tzinfo is None:
                        due = due.replace(tzinfo=datetime.timezone.utc)
                    is_overdue = due < now

                certainty = calculate_certainty(int(ms.open_issues), lead_time, due)

                repo_milestones.append({
                    "repo_name": str(full_name.split('/')[-1]),
                    "full_name": str(full_name),
                    "number": int(ms.number),
                    "title": str(ms.title),
                    "description": str(ms.description) if ms.description else "",
                    "open_issues": int(ms.open_issues),
                    "closed_issues": int(ms.closed_issues),
                    "due_on": ms.due_on.isoformat() if ms.due_on else None,
                    "progress": float(progress),
                    "is_overdue": bool(is_overdue),
                    "certainty": certainty,
                    "html_url": str(ms.html_url)
                })
            return repo_milestones
        except Exception:
            return []

    try:
        aggregated_milestones = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_repo_milestones, name) for name in repo_names]
            for future in futures:
                res = future.result()
                if res:
                    aggregated_milestones.extend(res)

        # Sort by due_on ascending, nulls last
        def sort_key(ms):
            return (ms['due_on'] is None, ms['due_on'])

        aggregated_milestones.sort(key=sort_key)

        _portfolio_milestones_cache[cache_key] = (now_ts, aggregated_milestones)
        return jsonify(aggregated_milestones), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
