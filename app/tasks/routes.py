from flask import Blueprint, request, session, jsonify
from github import Github
from ..workspace.utils import mask_token

bp = Blueprint('tasks', __name__)

def get_github_client():
    token = session.get('github_token')
    if not token:
        return None
    return Github(token)

@bp.route('/api/tasks', methods=['GET'])
def list_tasks():
    g = get_github_client()
    if not g:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user = g.get_user()
        login = user.login

        # Aggregation: Fetch from three categories
        # 1. Action Required: Review requested
        # 2. In Progress: Assigned to me
        # 3. My PRs: Authored by me

        action_required = g.search_issues(f"is:pr is:open review-requested:{login}")
        in_progress = g.search_issues(f"is:issue is:open assignee:{login}")
        my_prs = g.search_issues(f"is:pr is:open author:{login}")

        tasks = []

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

                    # Review Status
                    if category == "authored":
                        try:
                            reviews = pr.get_reviews()
                            states = [r.state for r in reviews if r.state != "COMMENTED"]
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
            tasks.append(normalize(item, "review_requested"))

        for item in in_progress:
            tasks.append(normalize(item, "assigned"))

        for item in my_prs:
            # Avoid duplicates if I'm assigned to my own PR or review requested (rare but possible)
            task_id = f"{item.repository.full_name}#{item.number}"
            if not any(t["id"] == task_id for t in tasks):
                tasks.append(normalize(item, "authored"))

        # Sort by updated_at desc
        tasks.sort(key=lambda x: x['updated_at'] if x['updated_at'] else '', reverse=True)

        return jsonify(tasks), 200
    except Exception as e:
        return jsonify({"error": mask_token(str(e))}), 500
