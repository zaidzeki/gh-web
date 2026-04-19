# Palette's Journal - GH-Web

## 2026-04-19 - [Loading States & Accessibility]
**Learning:** Users need immediate feedback for asynchronous operations to prevent double-submissions and feel in control. Accessible forms require explicit label-input associations and ARIA labels for non-labeled fields.
**Action:** Always implement a `toggleLoading` pattern for buttons and ensure all form elements have proper `id`/`for` pairings and `aria-label` where placeholders are used as the primary identifier.
