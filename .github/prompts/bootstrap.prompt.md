---
name: bootstrap
description: Review the current file only. Refactor the markup/CSS class usage to replace custom or redundant CSS classes with Bootstrap utility/component classes wherever possible.
---
Review the current file only. Refactor the markup/CSS class usage to replace custom or redundant CSS classes with Bootstrap utility/component classes wherever possible.

Goals:
- Preserve the existing visual styling, layout, responsiveness, and functionality.
- Use Bootstrap classes for spacing, flex/grid layout, alignment, typography, colors, buttons, forms, cards, badges, tables, visibility, and responsive behavior where appropriate.
- Remove custom classes only when their behavior is fully covered by Bootstrap.
- Keep custom classes when they provide project-specific styling that Bootstrap does not replicate exactly.
- Do not change business logic, event handlers, data bindings, IDs, accessibility attributes, or component structure unless required for class cleanup.
- Avoid broad rewrites; make the smallest safe changes.
- If Bootstrap cannot match a style exactly, keep the existing class and add a brief comment explaining why.
- After refactoring, summarize:
  1. Bootstrap classes added
  2. Custom classes removed
  3. Custom classes intentionally kept
  4. Any styling differences or risks

Please edit the file directly and ensure the result still renders the same.