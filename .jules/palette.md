# Palette Journal - Critical UX Learnings

## 2025-05-14 - [Initial Entry]
**Learning:** Initializing the Palette journal to track UX/accessibility improvements in GH-Web.
**Action:** Consistently document high-impact micro-UX enhancements and user feedback patterns.

## 2025-05-15 - [Dynamic UI Accessibility]
**Learning:** Dynamically generated form fields and list actions often miss critical accessibility attributes because they aren't part of the static HTML. Labels for dynamic inputs must be explicitly linked via `id` and `for` attributes, and action buttons in repeated list items (like "Delete") require unique `aria-label` or `title` attributes that include the item's name to provide context for screen readers.
**Action:** Always generate unique IDs for dynamic form inputs and include item-specific context in ARIA labels for list actions.
