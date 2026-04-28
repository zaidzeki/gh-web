## 2025-05-14 - Partial Path Traversal in Workspace Validation
**Vulnerability:** Path validation using `startswith` allowed access to sibling directories with a common prefix (e.g., `/tmp/repo` allowed access to `/tmp/repo-secret`).
**Learning:** `startswith` only performs string comparison and does not respect directory boundaries in path strings.
**Prevention:** Use `os.path.commonpath` to verify that a path is a subpath of another, as it correctly handles path components.

## 2025-05-15 - Sensitive Metadata Exposure via Workspace API
**Vulnerability:** The workspace file API allowed reading sensitive files within the `.git` directory (e.g., `.git/config`) because the path safety check only enforced the workspace boundary but not metadata isolation.
**Learning:** Cloned repositories on the server may contain sensitive credentials in `.git/config` if authentication tokens are part of the remote URL.
**Prevention:** Centralize path validation in a utility that not only enforces directory boundaries but also explicitly blocks access to forbidden metadata components like `.git` using path component analysis.

## 2025-05-16 - Path Traversal via Unsanitized Directory Components
**Vulnerability:** Even with path safety checks in file operations, the initial creation of workspace directories was vulnerable to path traversal if the repository name or session ID contained malicious sequences like `../../`.
**Learning:** Sanitizing individual path components with `secure_filename` BEFORE joining them is a critical first line of defense before performing any filesystem operations.
**Prevention:** Always apply `secure_filename` to user-controlled strings that are used to generate directory names or file paths, ensuring they remain within the intended parent directory.

## 2025-05-20 - Zip Slip Vulnerability in Repository Download
**Vulnerability:** The `download_repo` endpoint extracted zip archives from GitHub without validating that the extracted file paths remained within the workspace directory.
**Learning:** Standard library functions like `zipfile.extractall` do not automatically protect against path traversal sequences (e.g., `../../`) in archive member names, which can lead to files being written anywhere the process has permissions.
**Prevention:** Always iterate through archive members and validate their destination paths using a robust `is_safe_path` check before extraction.

## 2025-05-20 - Path Traversal via Scaffolding Template Variables
**Vulnerability:** The `render_template_dir` utility rendered relative file paths using user-provided context, allowing an attacker to inject traversal sequences into filename templates.
**Learning:** Even when the source template files are safe, dynamic rendering of filenames can introduce new traversal vectors if the resulting path is not validated against the target directory.
**Prevention:** Enforce `is_safe_path` validation on all dynamically generated paths during scaffolding, ensuring they never escape the intended destination root regardless of the rendering context.

## 2025-05-21 - Unintended Root Access via Empty Sanitized Filenames
**Vulnerability:** Using `secure_filename` on malicious inputs like `..` or `/` returns an empty string. When this empty string is joined to a base directory (e.g., `os.path.join('/base', '')`), it results in the base directory itself being used as the target, potentially allowing operations (like deletion or listing) on the entire root or session directory instead of a specific subdirectory.
**Learning:** `secure_filename` is not enough to ensure a path is safe if the resulting string is used to define a subdirectory. An empty result must be treated as an invalid/dangerous input.
**Prevention:** Always validate that the output of `secure_filename` is a non-empty string before using it to construct a path.

## 2025-05-22 - SSRF via Git Clone and Enhanced Token Masking
**Vulnerability:** The repository cloning endpoint allowed any `repo_url`, enabling protocol-based SSRF (e.g., `file://`) and access to internal services. Additionally, token masking was inconsistent across modules.
**Learning:** `git clone` can be used to read local files if protocols like `file://` are not restricted. Centralizing security logic like `mask_token` ensures consistent protection and allows for robust defense-in-depth measures like regex-based pattern matching for tokens.
**Prevention:** Enforce strict allow-lists for external URLs in cloning operations and centralize secret-masking utilities to ensure they are applied uniformly and robustly (including handling cases outside of request contexts).

## 2025-05-23 - DOM-based XSS via Attribute Injection
**Vulnerability:** The `escapeHTML` function in `app.js` relied on `div.textContent` to escape strings. While this handles `<` and `>`, it does not escape double or single quotes. This allowed attribute injection (e.g., `onmouseover`) when dynamic data was used inside HTML attributes within `innerHTML` template strings.
**Learning:** `textContent` is only safe for content between tags, not for content inside attributes. DOM-based XSS can occur even when "escaping" if the escaping doesn't account for the injection context.
**Prevention:** Always use a robust escaping function that covers ampersands, tags, and BOTH types of quotes when building HTML strings, or preferably use DOM APIs like `setAttribute` and `textContent` directly instead of `innerHTML`.
