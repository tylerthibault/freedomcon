"""
build.py — Pre-deploy asset minification
-----------------------------------------
Minifies all custom CSS and JS files in src/static/, writing *.min.* files
alongside the originals. Skips already-minified vendor files (bootstrap, etc.)
and any file that already ends in .min.css / .min.js.

Run manually:   python build.py
Run on deploy:  see nixpacks.toml (phases.build)
"""

import sys
from pathlib import Path

import rcssmin
import rjsmin

STATIC_DIR = Path(__file__).resolve().parent / "src" / "static"

# Directories to skip — pre-minified vendor assets
SKIP_DIRS = {"bootstrapcss", "bootstrapjs"}


def minify_css(src: Path) -> None:
    raw = src.read_text(encoding="utf-8")
    minified = rcssmin.cssmin(raw)
    dest = src.with_suffix("").with_suffix("") if src.stem.endswith(".min") else src.with_name(src.stem + ".min.css")
    dest.write_text(minified, encoding="utf-8")
    saved = len(raw) - len(minified)
    pct = (saved / len(raw) * 100) if raw else 0
    print(f"  CSS  {src.relative_to(STATIC_DIR)}  →  {dest.name}  ({saved:+,} bytes, {pct:.0f}% saved)")


def minify_js(src: Path) -> None:
    raw = src.read_text(encoding="utf-8")
    minified = rjsmin.jsmin(raw)
    dest = src.with_name(src.stem + ".min.js")
    dest.write_text(minified, encoding="utf-8")
    saved = len(raw) - len(minified)
    pct = (saved / len(raw) * 100) if raw else 0
    print(f"  JS   {src.relative_to(STATIC_DIR)}  →  {dest.name}  ({saved:+,} bytes, {pct:.0f}% saved)")


def main() -> int:
    print("=== Asset minification ===")

    css_count = js_count = 0

    # --- CSS ---
    for path in sorted((STATIC_DIR / "css").rglob("*.css")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.stem.endswith(".min"):
            continue  # already minified
        minify_css(path)
        css_count += 1

    # --- JS ---
    for path in sorted((STATIC_DIR / "js").rglob("*.js")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.stem.endswith(".min"):
            continue
        minify_js(path)
        js_count += 1

    print(f"\nDone: {css_count} CSS files, {js_count} JS files minified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
