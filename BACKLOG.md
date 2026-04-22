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
- [ ] **Epic: PR Review Sandboxing**
    - [ ] Implement `POST /api/workspace/stream-pr` for live PR reviews.
    - [ ] Add "Review" action to the PR management UI.

## P2: Feature
- [x] Create Frontend UI (Jinja2 templates, JS).
- [ ] Add toast notifications for API responses.

## P3: Polish
- [ ] Sphinx documentation.
- [ ] 100% test coverage.
