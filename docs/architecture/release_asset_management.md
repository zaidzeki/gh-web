# Architectural Design: Release Asset Management & Workspace Integration

## 1. Overview
The Release Asset Management module bridges the gap between the **Server-Side Workspace** (where code is built) and **GitHub Releases** (where code is distributed). It extends the existing `releases` blueprint to handle binary data transfers and asset metadata.

## 2. API Extensions

### 2.1. Asset Upload from Workspace
- **Endpoint:** `POST /api/repos/<path:full_name>/releases/<int:release_id>/assets`
- **Payload (JSON):**
```json
{
  "workspace_path": "dist/app-v1.0.0.zip",
  "name": "app-v1.0.0.zip",
  "label": "Optional label"
}
```
- **Responsibility:**
    1. Validate `workspace_path` is within the active repository boundaries.
    2. Read the file from the filesystem.
    3. Use `PyGithub`'s `upload_asset` method (which handles the `uploads.github.com` endpoint).
    4. Handle MIME type detection using `mimetypes`.

### 2.2. Asset Discovery & Management
- **Endpoint:** `GET /api/repos/<path:full_name>/releases/<int:release_id>/assets`
- **Response:** List of asset objects (name, size, download_count, id, url).
- **Endpoint:** `DELETE /api/repos/<path:full_name>/releases/assets/<int:asset_id>`
- **Responsibility:** Remove the asset from the release on GitHub.

## 3. Data Flow

### 3.1. Build-to-Release Flow
1. User executes a build in the Workspace (e.g., via the Editor or a future "Build" button).
2. User navigates to the Releases tab.
3. User opens the "Add Assets" modal for a specific (often draft) release.
4. User selects a file from the list (powered by `GET /api/workspace/files`).
5. Backend streams the file from the server's workspace to GitHub.

## 4. Security & Safety

### 4.1. Path Validation
All `workspace_path` parameters must be passed through `is_safe_path(workspace_dir, final_path)` to prevent unauthorized access to server files outside the repository.

### 4.2. Resource Management
- **Timeouts:** Asset uploads can take several minutes. The Flask request timeout and the `PyGithub` timeout must be increased for this specific endpoint.
- **Cleanup:** Temporary files (if any are created during the upload process) must be deleted immediately after the transfer completes.

## 5. UI Integration Patterns

### 5.1. Asset Table
Integrated into the `releasesList` display. Each release entry will have a "Manage Assets" button that opens a sub-view or modal.

### 5.2. Workspace Picker
A mini-explorer modal that allows the user to browse their current workspace and "Pick" a file, returning its relative path to the asset upload form.
