# Forge's Journal - Implementation Learnings

## 2025-05-23 - [PyGithub Deprecation]
**Learning:** `Github(token)` uses the deprecated `login_or_token` argument. Modern `PyGithub` (v2+) prefers `auth=github.Auth.Token(token)`.
**Action:** Use `github.Auth.Token` when initializing the GitHub client in new routes to future-proof the codebase and avoid deprecation warnings.

## 2025-05-23 - [Test Mocking Quirk]
**Learning:** When mocking PyGithub objects for JSON serialization in the backend, ensure the mock user object has an explicit `avatar_url` attribute to avoid 500 errors during API response generation in unit tests.
**Action:** Always verify mock objects have all attributes accessed during serialization.

## 2025-05-30 - [JSON Serialization of Mocks]
**Learning:** When mocking objects for JSON responses in Flask, MagicMock attributes like `html_url` or `commit.summary` must be explicitly set to primitive values (strings/ints). If left as default MagicMock objects, `jsonify()` will fail with a `TypeError`.
**Action:** Always verify that all attributes of mocked objects accessed during response generation are explicitly set to serializable types.

## 2026-05-01 - [Playwright & Bootstrap Tabs]
**Learning:** When verifying UI changes using Playwright, Bootstrap's `fade` class transitions may require a brief manual wait (e.g., `time.sleep(1)`) after clicking a tab to ensure elements are rendered and visible for assertions or screenshots.
**Action:** Use `time.sleep(1)` or a specific `wait_for` after switching tabs in Playwright verification scripts.

## 2025-06-03 - [GitHub Actions Pending Deployments API]
**Learning:** The GitHub REST API for pending deployments (`GET /repos/.../pending_deployments`) returns an object containing a `pending_deployments` key with a list of environments, not a bare list. Furthermore, PyGithub (v2.9.1) does not yet expose methods for reviewing deployments, requiring raw REST calls via `requests`.
**Action:** Always verify the structure of newer or preview GitHub REST APIs against documentation or Orchestra guides, and use the `requests` library for features missing in PyGithub.

## 2025-06-03 - [N+1 Bottleneck in Task Inbox]
**Learning:** Enrichment of the Task Inbox with workflow run IDs (`pending_run_id`) introduces an N+1 API call pattern (one search per merged PR). While acceptable for small inboxes, this can lead to performance degradation or rate-limiting in large environments.
**Action:** For enterprise-scale performance, consider batching metadata fetching or moving enrichment to a dedicated health/batch endpoint similar to `GET /api/repos/health`.
