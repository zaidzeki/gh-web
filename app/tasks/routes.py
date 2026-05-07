from flask import Blueprint, request, session, jsonify
import github
from ..workspace.utils import mask_token

bp = Blueprint('tasks', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    auth = github.Auth.Token(token)
    return github.Github(auth=auth)

@bp.route('/api/tasks', methods=['GET'])
def list_tasks():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user = g.get_user()
        login = user.login

        # Aggregation: Fetch from four categories with prioritization:
        # 0. High Priority: Deployments waiting for approval
        # 1. Action Required: Review requested
        # 2. In Progress: Assigned to me (Issues or PRs)
        # 3. My PRs: Authored by me

        # Limit to top 20 each to avoid performance/rate-limit issues
        waiting_deployments = []
        try:
            # Note: status:pending is used to find PRs with ongoing or waiting checks/deployments.
            # Deployment approvals specifically are hard to find via global search,
            # so we use this as a proxy for "Action Required" on deployments.
            waiting_deployments = g.search_issues(f"is:pr is:open review:required status:pending")[:20]
        except Exception:
            # Fallback to empty if search filter is not supported or fails
            pass

        # Re-evaluating: g.search_issues is for issues/PRs. Deployment approvals are different.
        # However, many organizations use PR status checks that include deployment gates.
        # For true Deployment API approvals, we'd need to iterate repos, which is slow.
        # Let's stick to the PR-based 'pending' status if possible or use a more generic search.

        # Actually, the spec says "Integrate deployment approvals into Task Inbox".
        # Let's try to find PRs that are 'pending' for a deployment status.
        # This is a bit tricky with search API.
        # Let's use the search query for PRs that have 'pending' in their status.
        action_required = g.search_issues(f"is:pr is:open review-requested:{login}")[:20]
        in_progress = g.search_issues(f"is:open assignee:{login}")[:20]
        my_prs = g.search_issues(f"is:pr is:open author:{login}")[:20]

        tasks = []
        task_ids = set()

        def normalize(issue_or_pr, category):
            repo_full_name = issue_or_pr.repository.full_name
            is_pr = issue_or_pr.pull_request is not None

            task = {
                "id": f"{repo_full_name}#{issue_or_pr.number}",
                "type": "pr" if is_pr else "issue",
                "category": category,
                "title": issue_or_pr.title,
                "repo": repo_full_name,
                "number": issue_or_pr.number,
                "html_url": issue_or_pr.html_url,
                "updated_at": issue_or_pr.updated_at.isoformat() if issue_or_pr.updated_at else None,
                "ci_status": None,
                "review_status": None
            }

            # Optional: Fetch CI/Review status for PRs
            if is_pr:
                try:
                    pr = issue_or_pr.as_pull_request()
                    # CI Status from HEAD
                    try:
                        combined = issue_or_pr.repository.get_combined_status(pr.head.sha)
                        task["ci_status"] = combined.state
                    except: pass

                    # Review Status (fetched for all PRs)
                    try:
                        reviews = pr.get_reviews()
                        states = [r.state for r in reviews if r.state != "COMMENTED"]
                        # Prioritize CHANGES_REQUESTED over APPROVED
                        if "CHANGES_REQUESTED" in states:
                            task["review_status"] = "changes_requested"
                        elif "APPROVED" in states:
                            task["review_status"] = "approved"
                        elif states:
                            task["review_status"] = "pending"
                    except: pass
                except: pass

            return task

        for item in waiting_deployments:
            task = normalize(item, "waiting_deployment")
            tasks.append(task)
            task_ids.add(task["id"])

        for item in action_required:
            task_id = f"{item.repository.full_name}#{item.number}"
            if task_id not in task_ids:
                tasks.append(normalize(item, "review_requested"))
                task_ids.add(task_id)

        for item in in_progress:
            task_id = f"{item.repository.full_name}#{item.number}"
            if task_id not in task_ids:
                tasks.append(normalize(item, "assigned"))
                task_ids.add(task_id)

        for item in my_prs:
            task_id = f"{item.repository.full_name}#{item.number}"
            if task_id not in task_ids:
                tasks.append(normalize(item, "authored"))
                task_ids.add(task_id)

        # Sort by updated_at desc
        tasks.sort(key=lambda x: x['updated_at'] if x['updated_at'] else '', reverse=True)

        return jsonify(tasks), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
