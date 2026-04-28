# CHANGELOG

## [0.1.0] - 2025-05-23
### Added
- Initial project structure.
- SPEC.md, NOTES.md, BACKLOG.md.
- Core Flask application with Blueprint structure.
- GitHub Authentication (PAT in session).
- Repository Management (Create).
- Pull Request Management (List, Create, Merge).
- Workspace Support (Clone, Download).
- Modification & File Operations (Patch, Upload, Archive, Commit).
- Single Page Application (SPA) dashboard.
- 98% Test Coverage with 60 tests (Unit, Integration, Playwright).
- Sphinx documentation.

## [0.2.0] - 2025-05-23
### Added
- Enhanced Workspace Git operations: Branch management (create/switch), Status indicators, and Pushing to remote.
- Frontend status badges for current branch and repository state (Clean/Modified).

## [0.3.0] - 2025-05-26
### Added
- Issue Linkage in IDD: Workspaces now track and display the active issue being fixed.
- Commit Automation: Automatically pre-fills commit messages with "Closes #N" when an issue is linked.
- Modernized Notifications: Replaced static alerts with Bootstrap Toast notifications for non-blocking feedback.
- **Expansion: Workspace Omni-Search**
    - High-performance code search using `ripgrep`.
    - Integrated Search Results modal with one-click navigation to the File Editor.
    - Context-aware result filtering with security path validation.
