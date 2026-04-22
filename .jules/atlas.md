## 2025-05-23 - [Inauguration]
**Learning:** Initializing the Atlas journal. GH-Web's architecture relies heavily on server-side state for workspaces. While this provides power, it creates a "black box" for the user.
**Action:** Prioritize visibility features (file explorers, status indicators) whenever server-side manipulation is involved to build user trust.

## 2025-05-24 - [Visibility as Trust]
**Learning:** In a 'Cloud IDE Lite' or automated management tool, the user's primary fear is "what did the tool just do to my code?". Providing granular visibility (diffs, history) is not just a feature, it's a security and trust requirement.
**Action:** Every major workspace automation (like template merging or patching) must be accompanied by a 'Review Changes' flow to empower the user.

## 2025-05-25 - [Static vs. Dynamic Assets]
**Learning:** Static templates are a "dead end" for complex projects that require customization. Adding dynamic parameter injection during template application turns simple boilerplate into a flexible project generator, significantly increasing user retention by reducing manual post-creation work.
**Action:** Repurpose existing file-copy logic by adding a "Transformation" layer to multiply the value of stored assets.
