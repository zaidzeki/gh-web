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

        # Aggregation: Fetch from three categories with prioritization:
        # 1. Action Required: Review requested
        # 2. In Progress: Assigned to me (Issues or PRs)
        # 3. My PRs: Authored by me
        # 4. Waiting Deployment: My merged PRs pending deployment/environment status
        #    Proxy: searching for merged PRs authored by me with status:pending

        # Limit to top 20 each to avoid performance/rate-limit issues
        action_required = g.search_issues(f"is:pr is:open review-requested:{login}")[:20]
        in_progress = g.search_issues(f"is:open assignee:{login}")[:20]
        my_prs = g.search_issues(f"is:pr is:open author:{login}")[:20]
        waiting_deployment = g.search_issues(f"is:pr is:merged status:pending author:{login}")[:20]

        tasks = []
        task_ids = set()

        def normalize(issue_or_pr, category):
            repo_full_name = str(issue_or_pr.repository.full_name)
            is_pr = issue_or_pr.pull_request is not None

            task = {
                "id": f"{repo_full_name}#{int(issue_or_pr.number)}",
                "type": "pr" if is_pr else "issue",
                "category": category,
                "title": str(issue_or_pr.title),
                "repo": repo_full_name,
                "number": int(issue_or_pr.number),
                "html_url": str(issue_or_pr.html_url),
                "updated_at": issue_or_pr.updated_at.isoformat() if issue_or_pr.updated_at else None,
                "ci_status": None,
                "review_status": None,
                "pending_run_id": None
            }

            # Optional: Fetch CI/Review status for PRs
            if is_pr:
                try:
                    pr = issue_or_pr.as_pull_request()
                    # CI Status from HEAD
                    try:
                        combined = issue_or_pr.repository.get_combined_status(str(pr.head.sha))
                        task["ci_status"] = str(combined.state)
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

        for item in action_required:
            task = normalize(item, "review_requested")
            tasks.append(task)
            task_ids.add(task["id"])

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

        for item in waiting_deployment:
            task_id = f"{item.repository.full_name}#{item.number}"
            if task_id not in task_ids:
                task = normalize(item, "waiting_deployment")

                # Enrich waiting_deployment tasks with pending run_id if available
                try:
                    repo = item.repository
                    # Search for workflow runs for the merge commit of this PR
                    # Merged PRs have a merge_commit_sha
                    pr = item.as_pull_request()
                    if pr.merge_commit_sha:
                        runs = repo.get_workflow_runs(event='push', status='waiting')
                        for run in runs:
                            if str(run.head_sha) == str(pr.merge_commit_sha):
                                task["pending_run_id"] = int(run.id)
                                break
                except:
                    pass

                tasks.append(task)
                task_ids.add(task_id)

        # Sort by updated_at desc
        tasks.sort(key=lambda x: x['updated_at'] if x['updated_at'] else '', reverse=True)

        return jsonify(tasks), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
