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
