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

## 2026-05-02 - [PyGithub PaginatedList Mocking]
**Learning:** PyGithub methods like `get_deployments()` return a `PaginatedList`, which has a `totalCount` attribute. Mocking these with a standard list in unit tests will cause `AttributeError` if the code accesses `totalCount`.
**Action:** Mock the return value of such methods with a `MagicMock` that has `totalCount` set and `__getitem__` implemented to return items.

## 2026-05-02 - [Playwright Mocking Strategy]
**Learning:** For frontend verification and UI testing in this repo, using `page.route` to mock backend API responses is much more reliable than trying to authenticate a real session. It decouples UI validation from backend state and live GitHub API behavior.
**Action:** Prefer `page.route` for all external data dependencies in Playwright scripts.
