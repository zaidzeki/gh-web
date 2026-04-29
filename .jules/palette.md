# Palette Journal - Critical UX Learnings

## 2025-05-14 - [Initial Entry]
**Learning:** Initializing the Palette journal to track UX/accessibility improvements in GH-Web.
**Action:** Consistently document high-impact micro-UX enhancements and user feedback patterns.

## 2025-05-15 - [Dynamic UI Accessibility]
**Learning:** Dynamically generated form fields and list actions often miss critical accessibility attributes because they aren't part of the static HTML. Labels for dynamic inputs must be explicitly linked via `id` and `for` attributes, and action buttons in repeated list items (like "Delete") require unique `aria-label` or `title` attributes that include the item's name to provide context for screen readers.
**Action:** Always generate unique IDs for dynamic form inputs and include item-specific context in ARIA labels for list actions.

## 2025-05-16 - [Keyboard Accessibility for Pseudo-buttons]
**Learning:** Using `<h6>` or other non-interactive elements as clickable items creates a "keyboard trap" where users cannot interact with them via tabbing. These elements require `role="button"`, `tabindex="0"`, and explicit keyboard listeners for 'Enter' and 'Space' to be truly accessible. Additionally, a global `:focus-visible` style is essential for these custom controls to provide visual feedback.
**Action:** When converting non-interactive elements to controls, always add standard ARIA attributes, keyboard listeners, and ensure they are covered by the global focus indicator styles in `style.css`.

## 2025-05-17 - [Contextual Accessibility for Repeated Actions]
**Learning:** Generic labels like "Issues", "PRs", or "Refresh" become ambiguous when repeated in a dashboard or across multiple tabs. Screen reader users need the full context (e.g., which repository or which part of the workspace) to be baked into the `aria-label`. Additionally, decorative search icons should be hidden with `aria-hidden="true"` to reduce noise.
**Action:** Always include item-specific names in `aria-label` for list-based actions and provide unique, context-aware labels for identically named buttons (like Refresh) that perform similar tasks in different areas.

## 2025-05-18 - [Visual Cues for Required Fields and Accessibility Parity]
**Learning:** Visual indicators like red asterisks are essential for form usability, but they must be paired with the `required` attribute for screen reader support. Furthermore, dashboard badges (like "Modified" or "3 PRs") are often invisible to assistive technologies if they aren't part of the primary element's `aria-label`. Including this dynamic state in the `aria-label` of the interactive list item provides immediate context to all users.
**Action:** Use a CSS-based `.required-label` for consistent visual cues across forms and ensure all dynamic visual badges are reflected in the `aria-label` of their parent interactive controls.

## 2026-04-28 - [Guided Input for Conventional Commits]
**Learning:** Providing real-time character counters with visual threshold feedback (e.g., turning red at 50 chars) significantly improves user compliance with Git subject line conventions without being restrictive.
**Action:** Use the dynamic character counter pattern for inputs where length conventions matter (like commit subjects or PR titles) and ensure the counter is initialized during programmatic pre-fills.

## 2026-04-28 - [Human-Readable Relative Timestamps]
**Learning:** Replacing static date strings with relative "time ago" formats (e.g., "2d ago") drastically reduces cognitive load for users scanning lists of repositories or issues. However, to maintain precision and accessibility, relative times should always be paired with a `title` attribute containing the full locale-specific timestamp and reflected in the `aria-label` of interactive items to ensure screen reader users have equal context.
**Action:** Use the `timeAgo` helper for activity-based dates in lists, and always supplement with `title` tooltips and updated ARIA labels.
