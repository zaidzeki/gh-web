# Palette's Journal - GH-Web

## 2026-04-19 - [Loading States & Accessibility]
**Learning:** Users need immediate feedback for asynchronous operations to prevent double-submissions and feel in control. Accessible forms require explicit label-input associations and ARIA labels for non-labeled fields.
**Action:** Always implement a `toggleLoading` pattern for buttons and ensure all form elements have proper `id`/`for` pairings and `aria-label` where placeholders are used as the primary identifier.

## 2026-04-20 - [Accessible Dynamic Trees and Alerts]
**Learning:** For dynamic tree structures, simply making elements look interactive with `cursor:pointer` is insufficient for accessibility. Elements must be explicitly focusable with `tabindex`, have appropriate ARIA roles (e.g., `role="button"`), and handle keyboard events (`Enter`/`Space`). Similarly, dynamically injected alerts must have `role="alert"` or `role="status"` to be announced by screen readers immediately.
**Action:** Ensure all dynamically generated interactive elements have proper focus management and ARIA roles. Always include keyboard event listeners alongside click listeners for custom interactive elements.
