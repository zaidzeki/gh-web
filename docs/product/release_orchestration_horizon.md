# 🌅 Horizon: Release & Changelog Orchestration Expansion Proposal

## 💡 The Pivot
GH-Web has evolved into a powerful tool for repository discovery, issue triage, and development (IDD). However, the software lifecycle doesn't end with merging a PR. We are pivoting into the **Production Readiness & Distribution** phase. By adding Release Management and Automated Changelog generation, we bridge the final gap between "Code Merged" and "Value Delivered", transforming GH-Web into a complete end-to-end delivery engine.

## ♻️ The Leverage
- **GitHub Releases API:** PyGithub already provides robust support for creating and listing releases.
- **GitHub Comparison API:** Reusing existing repository context to compare tags and branches for changelog generation.
- **Pull Request Context:** Leveraging merged PR metadata to categorize changes (Features, Fixes, Chore).
- **UI Patterns:** Reusing the searchable table and modal form patterns established in the PR and Issues tabs.

## 🚀 The Delta
- **Backend:**
    - `GET /api/repos/<full_name>/releases`: Lists existing releases.
    - `POST /api/repos/<full_name>/releases/generate-notes`: Uses GitHub's automated release notes engine to draft changelogs based on merged PRs.
    - `POST /api/repos/<full_name>/releases`: Creates a new release (tagging, naming, and publishing).
- **Frontend:**
    - **Releases Tab:** A dedicated view for browsing release history.
    - **Release Orchestrator:** A form to create new releases with a "Generate Draft" button that uses the comparison API to pre-fill notes.
    - **Dashboard Integration:** Repository list enriched with a quick link to the Releases tab and the latest release tag.

## 🎯 The Impact
- **End-to-End Workflow:** Users can now go from Issue -> Fix -> PR -> Release without ever leaving GH-Web.
- **Maintainer Velocity:** Automating the "Changelog Chore" removes a major friction point in the release process.
- **Strategic Positioning:** Solidifies GH-Web as a "DevOps Cockpit" that handles both the "Inner Loop" (dev) and the "Outer Loop" (release).
