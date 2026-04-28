# Architecture: Unified Conversation & Review Engine

## Overview
The Unified Conversation Engine provides a bridge between the GitHub API's commenting/review features and the GH-Web frontend. It ensures that users can participate in the social aspect of development without leaving the workspace context.

## Components

### 1. Backend API Layer
New routes are added to `app/issues/routes.py` and `app/prs/routes.py` to interface with `PyGithub`.

- **Issue/PR Comments (`GET & POST /api/repos/.../issues/<n>/comments`)**:
    - GitHub treats both Issues and PRs as "Issues" for general commenting.
    - `GET`: Fetches `issue.get_comments()` and maps them to a simplified JSON format (user, body, timestamp, avatar).
    - `POST`: Executes `issue.create_comment(body)`.

- **PR Reviews (`POST /api/repos/.../prs/<n>/reviews`)**:
    - `POST`: Executes `pr.create_review(body, event)` where event is `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`.

### 2. Frontend Conversation Manager
Implemented within `app/static/js/app.js`.

- **`ConversationModal`**: A single Bootstrap modal shared by both Issues and PRs.
- **Logic Flow**:
    1. User clicks "Comments" or "Review" button.
    2. JS fetches the current thread from the API.
    3. JS renders the thread with `escapeHTML` to prevent XSS.
    4. Modal presents a textarea for the reply.
    5. On submission, JS updates the thread locally and posts to the API.

## Data Mapping
The API returns a standardized `Comment` object:
```json
{
  "user": "username",
  "avatar_url": "...",
  "body": "Markdown text",
  "created_at": "ISO-8601"
}
```

## Security
- **XSS Prevention**: All comment bodies and usernames are passed through `escapeHTML` before rendering in the DOM.
- **CSRF**: Authenticated session ensures that only the logged-in user can post comments using their PAT.
- **Token Masking**: Error messages from the GitHub API are sanitized via `mask_token`.

## Scalability
- **Pagination**: For long threads, the API should eventually implement pagination (leveraging PyGithub's lazy loading).
- **Polling**: Initial implementation is fetch-on-demand; future versions could implement polling or WebSockets for live conversations.
