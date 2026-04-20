# Architecture: Workspace Management

## Overview
The Workspace Management module provides a window into the server-side filesystem used by GH-Web for repository manipulation. It ensures that users can verify their changes before committing and manage the workspace environment effectively.

## Data Flow
1.  **File Listing:**
    *   Frontend requests `GET /api/workspace/files`.
    *   Backend identifies the active workspace via session.
    *   Backend recursively walks the directory (excluding `.git`).
    *   Returns a nested JSON structure representing the file tree.

2.  **File Deletion:**
    *   Frontend sends `DELETE /api/workspace/files` with a `path`.
    *   Backend validates the path using `is_safe_path` and ensures it is not `.git`.
    *   Backend removes the file or directory.

3.  **File Content Retrieval:**
    *   Frontend requests `GET /api/workspace/files/content` with a `path`.
    *   Backend validates path.
    *   Backend reads the file and returns it as plain text or JSON.

## Security Considerations
*   **Path Traversal:** All file operations MUST use `is_safe_path` to prevent access to files outside the assigned workspace.
*   **Protected Files:** The `.git` directory must be protected from deletion to maintain repository integrity.
*   **Resource Limits:** File content retrieval should have a size limit (e.g., 1MB) to prevent server-side memory exhaustion and slow response times for large binary files.

## UI/UX Design
*   **Tree View:** Uses a simple nested `<ul>` structure or a lightweight JS library.
*   **Loading States:** Buttons and the tree itself should show spinners during async operations.
*   **Confirmations:** Deletion operations must require user confirmation.
