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
- [ ] **Epic: Collaborative PR Contribution**
    - [x] Enrich `GET /api/repos/full_name/prs` with head repo/branch metadata.
    - [ ] Implement multi-remote support in `stream-pr`.
    - [ ] Update `POST /api/workspace/push` to handle fork targets.
    - [ ] Add "Collaborative Mode" indicators to the UI.
- [x] **Epic: Dynamic Scaffolding Engine**
    - [x] Implement `render_template_dir` with Jinja2 support.
    - [x] Implement `manifest.json` parsing and API.
    - [x] Implement dynamic form generation in Frontend.

## P2: Feature
- [x] Create Frontend UI (Jinja2 templates, JS).
- [ ] Add toast notifications for API responses.

## P3: Polish
- [ ] Sphinx documentation.
- [ ] 100% test coverage.
