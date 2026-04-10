# Font Overview

## Goal
Minimize typography to a small, consistent system:
- **Regular font:** `Oswald`
- **Bold/action font:** `Fremont`
- **Allowed accent fonts (limited):** `Ghost Factory`, `American Scribe`

## Active Font Sources

### Google Fonts
- `Oswald` weights: `300`, `400`, `700`
- Loaded in: `src/templates/bases/public.html`

### Local Fonts (`src/static/fonts`)
- `Fremont-Osf Bold.ttf` → `Fremont`
- `Ghost Factory.ttf` → `Ghost Factory` (accent only)
- `americanscribe.ttf` → `American Scribe` (accent only)

## Token System (Single Source of Truth)
Defined in `src/static/css/main.css`:

- `--font-regular`: `Oswald, Arial, sans-serif`
- `--font-action`: `Fremont, Oswald, Arial, sans-serif`
- `--font-primary`: `var(--font-regular)`
- `--font-secondary`: `var(--font-action)`
- `--font-oswald-light`: `var(--font-regular)`
- `--font-oswald-bold`: `var(--font-regular)`
- `--font-fremont-osf-bold`: `var(--font-action)`
- `--font-ghost-factory`: `Ghost Factory, Fremont, Oswald, Arial, sans-serif`
- `--font-american-scribe`: `American Scribe, cursive`

## Usage Rules

1. **Body/regular text**
   - Use `var(--font-primary)` or `var(--font-oswald-light)`.
2. **Headings, CTAs, banner/action text**
   - Use `var(--font-secondary)` or `var(--font-action)`.
3. **Accent branding/script only**
   - `Ghost Factory` and `American Scribe` should be used sparingly for intentional identity moments.
4. **Do not add new font families** without design approval.
5. **Do not declare `@font-face` in component CSS**; keep declarations centralized in `src/static/css/main.css`.

## Key Files Updated in This Consolidation
- `src/templates/bases/public.html` (Google font load simplified to Oswald)
- `src/static/css/main.css` (canonical tokens and `@font-face` definitions)
- `src/static/css/components/freedom_con_shell.css` (removed duplicate `@font-face`; token-based fonts)
- `src/static/css/components/landing-variant-12.css` (removed duplicate `@font-face`; replaced legacy families with tokenized Fremont/Oswald)

## Verification Checklist
- Search for banned legacy families in active CSS:
  - `Work Sans`
  - `Newsreader`
  - `Nickel Gothic`
- Ensure only one place defines `@font-face`:
  - `src/static/css/main.css`
- Confirm route pages render with expected hierarchy:
  - `/`, `/speakers`, `/faqs`, `/artists`, `/accommodations`, `/where`, `/vendors`, `/worship`, `/tickets`

## Future Cleanup (Optional)
- If branding direction allows, reduce accent fonts further by replacing `Ghost Factory` and/or `American Scribe` usages with `Fremont`.
