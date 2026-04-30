# Dev Procedures

## 1. Convert Images to WebP

Converts all PNG/JPG in `src/static/img/` to optimized WebP files using Pillow.

### Basic usage (skip already-converted):
```bash
python optimize_images.py
```

### Options:
```bash
# Preview what would be converted without writing files
python optimize_images.py --dry-run

# Reconvert even if .webp already exists
python optimize_images.py --force

# Override compression quality (default: 80)
python optimize_images.py --quality 85

# Override global max width (default: 1600px)
python optimize_images.py --max-width 1200
```

### Per-subdirectory resize rules (configured in optimize_images.py):
| Directory | Max Width |
|---|---|
| `speakers/` | 600px |
| `social_proof/` | 900px |
| `conference_info/` | 1200px |
| everything else | 1600px |

### Notes:
- `favicon/` is skipped entirely
- Transparency (PNG alpha) is preserved
- Pillow must be installed: `pip install Pillow>=10.0`
- This also runs automatically during the nixpacks build phase via `build.py`

---

## 2. Minify CSS / JS

Minification is done manually. The source files and their minified counterparts are:

| Source | Minified Output |
|---|---|
| `src/static/css/main.css` | `src/static/css/main.min.css` |
| `src/static/js/main.js` | `src/static/js/main.min.js` |
| `src/static/js/popup.js` | `src/static/js/popup.min.js` |
| `src/static/js/venue_map.js` | `src/static/js/venue_map.min.js` |
| `src/static/js/venue_map_svg.js` | `src/static/js/venue_map_svg.min.js` |

### Recommended tools:

**CSS — using `csso-cli`:**
```bash
npx csso src/static/css/main.css --output src/static/css/main.min.css
```

**JS — using `terser`:**
```bash
npx terser src/static/js/main.js -o src/static/js/main.min.js --compress --mangle
npx terser src/static/js/popup.js -o src/static/js/popup.min.js --compress --mangle
npx terser src/static/js/venue_map.js -o src/static/js/venue_map.min.js --compress --mangle
npx terser src/static/js/venue_map_svg.js -o src/static/js/venue_map_svg.min.js --compress --mangle
```

> No npm `package.json` is required — `npx` will pull the tools on demand.

---

## 3. Running the Dev Server

```bash
python run.py
```
