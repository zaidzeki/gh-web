# BACKLOG

## P0: Immediate
- [x] Initialize Python environment and dependencies (`flask`, `PyGithub`, `GitPython`, `pytest`, etc.).
- [x] Implement core Flask application with Blueprints structure.
- [x] Implement Authentication (GitHub PAT in session).
- [x] Implement Repository Management (Create repo).

## P1: Critical
- [x] Implement Pull Request Management (List, Create, Merge).
- [x] Implement Workspace Support (Clone, Download).
- [x] Implement Modification & File Operations (Patch, Upload, Commit).
- [x] **Epic: Workspace Visibility & Management**
    - [x] List workspace files in a tree-view.
    - [x] Delete files/folders from workspace.
    - [x] View file content in modal.
    - [x] Enhanced Git support (Branching, Status, Pushing).
- [x] **Epic: Workspace Composition & Cloud IDE**
    - [x] Direct file editing in browser.
    - [x] Composite scaffolding (merging templates).
    - [x] Remote template import from GitHub.
- [x] **Epic: Workspace Git Visibility & Transparency**
    - [x] Implement `GET /api/workspace/diff` for uncommitted changes.
    - [x] Implement `GET /api/workspace/history` for recent commits.
    - [x] Implement `POST /api/workspace/revert` to discard changes.
    - [x] Add "View Diff" and "History" modals to the Workspace UI.
    - [x] Add "Discard Changes" safety action to the Workspace UI.
- [x] **Epic: PR Review Sandboxing**
    - [x] Implement `POST /api/workspace/stream-pr` for live PR reviews.
    - [x] Add "Review" action to the PR management UI.
- [x] **Epic: Collaborative PR Contribution**
    - [x] Enrich `GET /api/repos/full_name/prs` with head repo/branch metadata.
    - [x] Implement multi-remote support in `stream-pr`.
    - [x] Update `POST /api/workspace/push` to handle fork targets.
    - [x] Add "Collaborative Mode" indicators to the UI.
- [x] **Epic: Repository Discovery & Dashboard**
    - [x] Implement `GET /api/user` for profile discovery.
    - [x] Implement `GET /api/repos` for repository listing and search.
    - [x] Implement `GET /api/workspace/portfolio` for multi-workspace monitoring.
    - [x] Create Dashboard UI with searchable repo list and active workspace summary.
    - [x] Integrate user profile (avatar/login) into the application header.
    - [x] Include PR counts in repo discovery.
    - [x] Implement quick actions (Sync/Discard) in workspace portfolio.
- [x] **Epic: Dynamic Scaffolding Engine**
    - [x] Implement `render_template_dir` with Jinja2 support.
    - [x] Implement `manifest.json` parsing and API.
    - [x] Implement dynamic form generation in Frontend.
- [x] **Epic: Issue-Driven Development (IDD)**
    - [x] Implement `POST /api/workspace/setup-issue-fix` for automated branch creation.
    - [x] Add "Fix" action to Issues table in UI.
    - [x] Implement automated tab navigation and workspace refresh after "Fix" click.
- [x] **Epic: Workspace Omni-Search**
    - [x] Implement `GET /api/workspace/search` using `ripgrep`.
    - [x] Create Omni-Search UI in Workspace tab.
    - [x] Implement Search Results modal with navigation to Editor.
- [x] **Epic: Contextual Conversations & Feedback Loop**
    - [x] Implement `GET /api/repos/.../issues/<n>/comments` for thread fetching.
    - [x] Implement `POST /api/repos/.../issues/<n>/comments` for replying.
    - [x] Implement `POST /api/repos/.../prs/<n>/reviews` for formal reviews.
    - [x] Create Unified Conversation Modal in Frontend.
    - [x] Integrate "Comments" actions into Issues and PR tables.
    - [x] Integrate contextual "Conversation" button into Workspace for active tasks.
- [x] **Epic: Task Orchestration & Unified Inbox**
    - [x] Implement `GET /api/tasks` for multi-category aggregation.
    - [x] Enrich task data with CI and Review status.
    - [x] Create Task Inbox UI on the Dashboard.
    - [x] Integrate "Fix" and "Review" quick-actions into the Task Inbox.
- [ ] **Epic: Workflow & CI/CD Orchestration**
    - [ ] Implement `GET /api/repos/.../actions/workflows` for discovery.
    - [ ] Implement `GET /api/repos/.../actions/runs` for monitoring.
    - [ ] Implement `POST /api/repos/.../actions/workflows/<id>/dispatch` for manual triggers.
    - [ ] Create Actions Tab UI with searchable run history.
    - [ ] Implement dynamic dispatch forms based on workflow inputs.
    - [ ] Integrate CI status badges into Dashboard and Workspace header.

## P2: Feature
- [x] Create Frontend UI (Jinja2 templates, JS).
- [x] Add toast notifications for API responses.

## P3: Polish
- [ ] Sphinx documentation.
- [ ] 100% test coverage.
