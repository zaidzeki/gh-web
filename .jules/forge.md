## 2025-06-01 - [GitHub API Path Converter]
**Learning:** GitHub repository full names contain slashes (e.g., `owner/repo`). Flask routes handling these must use the `<path:full_name>` converter to capture the entire string correctly.
**Action:** Use `@bp.route('/api/repos/<path:full_name>/...')` for any repo-contextual endpoints.

## 2025-06-01 - [Frontend Array Validation]
**Learning:** When iterating over API responses in `app/static/js/app.js`, failing to check `Array.isArray()` can lead to `TypeError` if the API returns an error object instead of a list.
**Action:** Always wrap list iterations in `if (Array.isArray(data)) { ... }`.
