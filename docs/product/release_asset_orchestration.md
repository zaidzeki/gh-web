# PRD: Release Asset Orchestration & Artifact Governance

## 1. Problem Statement
GH-Web has successfully implemented "Release & Changelog Orchestration," allowing users to draft notes and create GitHub Releases. However, a "Release" is often more than just text; it frequently includes binary artifacts, installers, or distribution packages. Currently, users must build these artifacts in their workspace and then leave GH-Web to manually upload them to GitHub. This "Last Mile" friction prevents GH-Web from being a truly complete delivery engine.

## 2. Objectives
- **Complete the Release Loop:** Enable users to attach workspace files directly to GitHub Releases.
- **Leverage the Build Environment:** Turn the server-side workspace into a functional build-and-distribute station.
- **Enhance Visibility:** Provide a unified view of all assets associated with a release, including their download counts and sizes.

## 3. User Stories
- **As a Maintainer,** I want to select a compiled artifact from my server-side workspace and upload it to a GitHub Release so I can distribute my software without manual context switching.
- **As a Release Manager,** I want to view a list of all assets currently attached to a release to ensure all required binaries are present before publishing.
- **As a Developer,** I want to delete an outdated or incorrect asset from a draft release directly from the dashboard.

## 4. Proposed Features

### 4.1. Workspace Asset Selector
- Integrate a "Select from Workspace" button into the Create/Edit Release UI.
- Allow users to browse the current active workspace and pick one or more files to be uploaded as assets.

### 4.2. Release Asset Management
- In the Release History list, add an "Assets" toggle or modal for each release.
- Display a table of assets including:
    - File Name
    - Size (formatted)
    - Download Count
    - "Delete" action for maintainers.

### 4.3. Artifact Governance (Phase 3)
- **Automatic Upload:** Option to specify a `glob` pattern (e.g., `dist/*.zip`) to automatically upload matching files during release creation.
- **Asset Integrity:** Surface warnings if a release is created without any assets (for repositories that typically include them).

## 5. Acceptance Criteria
- [ ] Backend API `POST /api/repos/<full_name>/releases/<id>/assets` supports uploading a file from the workspace.
- [ ] Backend API `GET /api/repos/<full_name>/releases/<id>/assets` returns a list of attached assets.
- [ ] Backend API `DELETE /api/repos/<full_name>/releases/assets/<id>` allows removing an asset.
- [ ] UI allows users to select a workspace file and trigger the upload.
- [ ] Release list displays asset counts and provides access to asset management.

## 6. Technical Considerations
- **Binary Streaming:** Use streaming to handle large asset uploads without exhausting server memory.
- **MIME Type Detection:** Automatically detect the correct `Content-Type` for assets (e.g., using `mimetypes` library).
- **Security:** Strictly validate that any file selected from the workspace is within the allowed repository directory boundaries.
- **GitHub API Limits:** Asset uploads use a different endpoint (`uploads.github.com`). `PyGithub` handles this, but timeouts should be adjusted for large files.
