# Strategic Pivot: From Development Tool to Delivery Engine

## Context
GH-Web started as a utility for managing GitHub repositories and workspaces. It successfully expanded into Issue-Driven Development (IDD), bridging the gap between triage and coding. However, the data shows that users still "leak" out of the application to GitHub.com for the final mile: **Releasing the software**.

## The Opportunity: Release Orchestration
Releasing software is often a manual, error-prone process involving:
1. Identifying which PRs were merged since the last release.
2. Manually drafting a changelog.
3. Tagging the repository.
4. Publishing the release assets.

By capturing this phase, GH-Web completes the "Project Loop".

## Strategic Value
1. **Retention:** Users spend more time in GH-Web because it handles the *entire* lifecycle.
2. **Data Ownership:** We can now correlate Issues -> PRs -> Releases, providing insights into development velocity.
3. **Platform Maturity:** Release management is a "Tier 1" feature of platforms like GitLab or GitHub. Adding it elevates GH-Web from a "wrapper" to an "orchestrator".

## Future Adjacencies
- **Deployment Triggers:** Bridging Releases to GitHub Actions or external CI/CD platforms.
- **Dependency Health:** Surfacing security alerts and out-of-date packages as "Release Blockers".
- **Asset Management:** Handling binary distribution directly from the workspace.

## Conclusion
The move into Release Orchestration is a high-ROI adjacency. It reuses 90% of our existing GitHub integration while unlocking 100% of the "Delivery" persona.
