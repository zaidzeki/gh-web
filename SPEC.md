# GH-Web Technical Specification

## 1. Overview
**GH-Web** is a web-based graphical interface and backend service for managing GitHub repositories, Pull Requests, and server-side local workspaces. Built with Flask, it uses `PyGithub` to interface with the GitHub API. It allows users to perform remote repository management and execute local repository modifications (via a server-side workspace), including file uploads, archive extraction, patch application, and git commits directly from their web browser.

## 2. Technology Stack
### Backend
*   **Web Framework:** Python / Flask
*   **GitHub Integration:** `PyGithub` (interacting with GitHub REST API v3)
*   **Git Operations:** `GitPython` or standard `subprocess` for executing git commands within the server workspace.
*   **File Handling:** Standard Python libraries (`os`, `shutil`, `zipfile`, `tarfile`) and `Werkzeug` for handling multipart file uploads.

### Frontend
*   **Structure:** HTML5 (Flask Jinja2 Templates)
*   **Styling:** CSS3 (Custom styles or a lightweight framework like Bootstrap/Tailwind for UI components)
*   **Interactivity:** Vanilla JavaScript (Fetch API for asynchronous operations, dynamic DOM updates, and form handling).

## 3. Architecture & Concepts
*   **Authentication:** Users provide a GitHub Personal Access Token (PAT) via the web UI, which is securely stored in the Flask session.
*   **Server-Side "Local" Workspace:** The "local repo" functions refer to cloning/downloading the repository onto the **server's filesystem**. Modifications, patch applications, and commits happen on the server, which then pushes the changes back to remote GitHub.

## 4. Functional Requirements & Web Interface

### 4.1. Repository Management
*   **UI Component:** A form to configure and trigger repository creation.
*   **Route:** `POST /api/repos/create`
*   **Parameters:** `name` (text), `description` (text), `visibility` (radio: public/private).
*   **Behavior:** Uses `PyGithub` to create the repository and updates the UI via JS to confirm creation.

### 4.2. Pull Request (PR) Management
*   **List PRs**
    *   **UI Component:** A dynamically populated table/list showing open/closed PRs.
    *   **Route:** `GET /api/repos/<repo_owner>/<repo_name>/prs`
*   **Create PR**
    *   **UI Component:** A modal or dedicated page with a form.
    *   **Route:** `POST /api/repos/<repo_owner>/<repo_name>/prs`
    *   **Payload:** `title`, `body`, `head` (source branch), `base` (target branch).
*   **Merge PR**
    *   **UI Component:** A "Merge" button next to an open PR in the list.
    *   **Route:** `POST /api/repos/<repo_owner>/<repo_name>/prs/<pr_number>/merge`
    *   **Payload:** `commit_message`, `merge_method` (merge/squash/rebase).

### 4.3. Local Workspace Support (Server-Side)
*   **Clone Repository**
    *   **Route:** `POST /api/workspace/clone`
    *   **Payload:** `repo_url`
    *   **Behavior:** Invokes `git clone` to a designated workspace directory on the server, allowing subsequent local git operations.
*   **Download Repository**
    *   **Route:** `POST /api/workspace/download`
    *   **Payload:** `repo_name`, `ref` (branch/tag)
    *   **Behavior:** Fetches the repo as an archive via `PyGithub` and stores it locally on the server (no `.git` directory included).

### 4.4. Modifications & File Operations
These operations apply to the repository currently active in the server's workspace.

*   **Apply Patch File**
    *   **UI Component:** File upload input restricted to `.patch`/`.diff`.
    *   **Route:** `POST /api/workspace/patch`
    *   **Behavior:** Uploads the patch file to the server; backend executes `git apply <patch_file>` against the active cloned workspace.
*   **Upload Files**
    *   **Single File:**
        *   **UI Component:** File picker and a text input for the destination path.
        *   **Route:** `POST /api/workspace/upload/file`
        *   **Payload:** `file` (multipart form data), `target_path` (relative path in repo).
        *   **Behavior:** Saves the file to the specific directory in the server workspace.
    *   **As Archive (Extract to CWD):**
        *   **UI Component:** File picker (restricted to `.zip`, `.tar.gz`) and text input for `target_cwd`.
        *   **Route:** `POST /api/workspace/upload/archive`
        *   **Payload:** `archive` (multipart form data), `target_cwd` (Current Working Directory relative to repo root).
        *   **Behavior:** Extracts the contents of the archive into the designated `target_cwd`.
*   **Commit Changes**
    *   **UI Component:** A form specifying the commit message.
    *   **Route:** `POST /api/workspace/commit`
    *   **Payload:** `commit_message`
    *   **Behavior:** Stages all changes (`git add .`) and creates a commit (`git commit -m`). (Note: Pushing can be bundled here or as a separate step).
*   **List Workspace Files**
    *   **UI Component:** A tree-view explorer in the Workspace tab.
    *   **Route:** `GET /api/workspace/files`
    *   **Behavior:** Recursively lists files and directories in the active workspace, excluding the `.git` folder.
*   **Delete Workspace File/Folder**
    *   **UI Component:** "Delete" icon/button in the file explorer.
    *   **Route:** `DELETE /api/workspace/files`
    *   **Payload:** `path` (relative to workspace root).
    *   **Behavior:** Permanently removes the file or directory from the server workspace.
*   **View File Content**
    *   **UI Component:** Modal popup when a file is clicked in the explorer.
    *   **Route:** `GET /api/workspace/files/content?path=...`
    *   **Behavior:** Returns the raw text content of the specified file.

## 5. API Route Summary (Backend)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Renders the main `index.html` frontend UI. |
| `POST` | `/login` | Stores the GitHub token in the user's Flask session. |
| `POST` | `/api/repos` | Creates a new GitHub repository. |
| `GET` | `/api/repos/<full_name>/prs` | Returns JSON list of Pull Requests. |
| `POST` | `/api/repos/<full_name>/prs` | Creates a Pull Request. |
| `POST` | `/api/repos/<full_name>/prs/<id>/merge` | Merges a specific PR. |
| `POST` | `/api/workspace/clone` | Clones a repository to the server workspace. |
| `POST` | `/api/workspace/download` | Downloads repository archive to the server. |
| `POST` | `/api/workspace/modify/patch` | Uploads and applies a patch file. |
| `POST` | `/api/workspace/modify/upload` | Uploads a single file to a specific path. |
| `POST` | `/api/workspace/modify/archive` | Uploads and extracts an archive to a given CWD. |
| `POST` | `/api/workspace/commit` | Commits (and optionally pushes) local modifications. |
| `GET` | `/api/workspace/files` | Lists files in the active workspace. |
| `DELETE` | `/api/workspace/files` | Deletes a file/folder in the workspace. |
| `GET` | `/api/workspace/files/content` | Retrieves text content of a file. |

## 6. Frontend Structure

*   **`templates/index.html`:** The primary Single Page Application (SPA) or dashboard.
*   **`static/css/style.css`:** Styles detailing layout grids, modal popups for forms, and notification banners.
*   **`static/js/app.js`:** 
    *   Handles tab switching (e.g., Repo View, PR View, Workspace View).
    *   Intercepts form submissions (`e.preventDefault()`).
    *   Packages file uploads into `FormData` objects.
    *   Uses `fetch()` to communicate with Flask `/api/` endpoints.
    *   Displays success/error toast notifications based on HTTP response status.

## 7. Error Handling & Security Measures

*   **Session Security:** The Flask app must configure `SECRET_KEY` and enforce secure cookies to protect the user's GitHub Token.
*   **Path Traversal Prevention:** When processing Single File Uploads and Archive Extractions, the Flask backend must use `werkzeug.utils.secure_filename` and validate that the `target_path` or `target_cwd` safely resolves *inside* the workspace directory to prevent writing files to arbitrary server locations (e.g., preventing Zip Slip).
*   **Git Locks & Concurrency:** If multiple users access the app, the backend must use session-specific workspace directories (e.g., `/tmp/gh-web-workspaces/<session_id>/<repo_name>`) to prevent users from conflicting with each other's git operations.
*   **API Error Propagation:** `PyGithub` errors (like 401 Unauthorized or 422 Validation Failed) must be caught by Flask and returned as clear JSON error messages (`{"error": "..."}`), which the JavaScript frontend will render as UI alerts.
