# Architecture: Dynamic Template Engine

## Overview
The Dynamic Template Engine extends the existing Workspace Templates by adding a transformation layer. Instead of direct file copies, the engine parses template files as Jinja2 templates and performs context-aware rendering of both content and file paths.

## Components

### 1. Manifest Parser
*   **Location:** Backend (`app/workspace/utils.py` or within routes).
*   **Function:** Checks for `manifest.json` in the template root. If present, it validates the schema and extracts variable definitions to send to the frontend for form generation.

### 2. Transformation Layer
*   **Logic:**
    1.  Recursively walk the template directory.
    2.  For every file/directory path:
        *   Render the path string using Jinja2 and the provided context.
        *   Create the target directory structure.
    3.  For every file:
        *   Read the content.
        *   If it's a text file (determined by extension or mime-type), render it with Jinja2.
        *   Write the rendered content to the transformed target path.

### 3. Context Provider
*   **Function:** Gathers input from the user (via `POST` body) and supplements it with system variables (e.g., `today`, `active_user`, `repo_name`).

## Data Flow
1.  **Selection:** User selects a template in the UI.
2.  **Manifest Fetch:** Frontend calls `GET /api/workspace/templates/<name>/manifest`.
3.  **Form Generation:** Frontend renders input fields for each variable found in the manifest.
4.  **Submission:** User submits the form. `POST /api/workspace/apply-template` now includes a `context` object.
5.  **Execution:** Backend performs the transformed copy.

## Security Considerations
*   **SSTI (Server-Side Template Injection):** Use a sandboxed Jinja2 environment if possible. Ensure that template rendering cannot access sensitive system objects or environment variables not explicitly provided in the context.
*   **Path Traversal:** After rendering paths, re-validate that the final target path still resides within the workspace boundary using `is_safe_path`.
*   **Resource Limits:** Limit the size of files processed by Jinja2 to prevent CPU exhaustion on very large files.
