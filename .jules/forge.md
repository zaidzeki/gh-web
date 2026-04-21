# Forge's Journal - Critical Learnings Only

## 2025-05-23 - Initializing Forge Journal
**Learning:** GH-Web's server-side workspace relies on manual Git operations. While basic commit functionality exists, the lack of branch management and push capabilities prevents a full development loop from the web interface.
**Action:** Implement branch and push operations to complete the remote-local-remote synchronization cycle.

## 2026-04-21 - Handling Git Visibility in Empty Repositories
**Learning:** To retrieve a unified diff of all uncommitted changes (staged and unstaged) in a Git repository without any commits, diffing against 'HEAD' fails. Instead, diff against the Git empty tree hash '4b825dc642cb6eb9a060e54bf8d69288fbee4904'.
**Action:** Use the empty tree hash for diffs and manual cleanup for reverts in brand-new workspaces to ensure correct behavior before the first commit.
