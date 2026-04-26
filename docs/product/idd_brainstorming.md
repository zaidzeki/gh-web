# Brainstorming: Issue-Driven Development (IDD)

## Problem Statement
Currently, GH-Web allows users to browse issues and manage workspaces, but these two workflows are disconnected. When a user identifies an issue they want to fix, they must:
1. Copy the repository name.
2. Navigate to the "Workspace" tab.
3. Paste the repository name and clone/download it.
4. Manually create a new branch for the fix.
5. Remember the issue number for the eventual pull request.

This "Manual Bridge" creates friction and increases the cognitive load on the user, especially when managing multiple repositories and issues.

## Proposed Solution: The "Fix" Action
Introduce a "Fix" action directly within the Issues tab. This action acts as a shortcut that automates the setup of a development environment for a specific issue.

### The Workflow
1. **User Action:** The user clicks the "Fix" button on an issue in the "Issues" tab.
2. **Automated Setup:**
   - The system ensures the repository is cloned/active in the server-side workspace.
   - The system creates a new git branch named `fix/issue-{number}` (e.g., `fix/issue-42`) branched from the repository's default branch.
   - The system sets this repository as the "Active Repository" for the session.
3. **Seamless Transition:** The UI automatically switches the user to the "Workspace" tab.
4. **Contextual Awareness:** The Workspace Explorer refreshes to show the files for the newly branched repository, ready for editing.

## Benefits
- **Reduced Friction:** Eliminates 4-5 manual steps.
- **Naming Consistency:** Enforces a standard branch naming convention (`fix/issue-N`).
- **Improved Context:** Bridges the gap between "Triage" (Issues) and "Implementation" (Workspace).
- **Higher Velocity:** Allows maintainers and contributors to jump from problem to solution in a single click.

## Future Considerations
- **Issue Linkage:** Automatically prepending "Closes #N" to the commit message form when a "Fix" session is active.
- **PR Automation:** Pre-filling the PR creation form with the issue title and "Closes #N" description.
- **Task List Integration:** Surfacing the active issue title in the Workspace header.
