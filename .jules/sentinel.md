## 2025-05-14 - Partial Path Traversal in Workspace Validation
**Vulnerability:** Path validation using `startswith` allowed access to sibling directories with a common prefix (e.g., `/tmp/repo` allowed access to `/tmp/repo-secret`).
**Learning:** `startswith` only performs string comparison and does not respect directory boundaries in path strings.
**Prevention:** Use `os.path.commonpath` to verify that a path is a subpath of another, as it correctly handles path components.

## 2025-05-15 - Sensitive Metadata Exposure via Workspace API
**Vulnerability:** The workspace file API allowed reading sensitive files within the `.git` directory (e.g., `.git/config`) because the path safety check only enforced the workspace boundary but not metadata isolation.
**Learning:** Cloned repositories on the server may contain sensitive credentials in `.git/config` if authentication tokens are part of the remote URL.
**Prevention:** Centralize path validation in a utility that not only enforces directory boundaries but also explicitly blocks access to forbidden metadata components like `.git` using path component analysis.
