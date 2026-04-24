# Analysis: The "Manual Entry Wall" Friction Point

## 1. Executive Summary
Currently, GH-Web requires users to manually type or paste full repository names (e.g., `octocat/Hello-World`) to perform core actions like listing Pull Requests or cloning repositories. This "Manual Entry Wall" represents a significant barrier to entry and a source of operational friction that degrades the user experience and limits the product's perceived value as a management hub.

## 2. Friction Points

### 2.1. Discovery Paralysis
Users often do not remember the exact spelling or capitalization of their repository names, especially in large organizations. Forcing them to navigate back to GitHub.com to find the name before returning to GH-Web breaks the workflow and increases the risk of churn.

### 2.2. Error Proneness
Manual typing is prone to errors. A single typo in the `owner/repo` string leads to a "Repository not found" error, which, while technically correct, feels like a failure of the application to be helpful.

### 2.3. Onboarding Friction
New users who login with a PAT are greeted with empty forms. There is no "immediate value" or "quick start" path. They must already know exactly what they want to do and where they want to do it.

### 2.4. Lack of Portfolio Overview
Users have no way to see the "health" of their repository portfolio within GH-Web. They cannot see which repositories have open PRs or which workspaces are currently active without checking them one by one.

## 3. Impact on Metrics
- **User Retention:** High friction in common tasks leads to lower daily active usage (DAU).
- **Task Completion Time:** The "GH-Web -> GitHub -> GH-Web" loop significantly increases the time it takes to perform simple actions like reviewing a PR.
- **Error Rate:** A measurable portion of 404 errors in the API logs likely stems from typos in manual entry.

## 4. Strategic Recommendation: "Discovery-First" UX
GH-Web must pivot from a **"Command-Line-Style"** interface (where the user provides the target) to a **"Dashboard-Style"** interface (where the application presents targets to the user).

### Key Transitions:
- **From:** "Enter repo name to see PRs" -> **To:** "Select from your active repositories."
- **From:** "Enter repo name to clone" -> **To:** "Search your GitHub portfolio."
- **From:** "Manual Entry" -> **To:** "Autosuggest & Discovery."
