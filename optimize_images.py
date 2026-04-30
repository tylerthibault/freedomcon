#!/usr/bin/env python3
"""
optimize_images.py — Bulk PNG/JPG → WebP conversion for src/static/img/

Usage:
    python optimize_images.py                   # convert everything (skip if .webp exists)
    python optimize_images.py --dry-run         # preview without writing files
    python optimize_images.py --force           # reconvert even if .webp already exists
    python optimize_images.py --quality 85      # override compression quality (default 80)
    python optimize_images.py --max-width 1200  # override global max width (default 1600)

Resize rules (can be overridden per-subdirectory via SUBDIR_MAX_WIDTHS below):
    img/speakers/  → 600px wide max
    all others     → 1600px wide max (or --max-width value)
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit(
        "ERROR: Pillow is not installed. Run:  pip install Pillow>=10.0"
    )

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Root of all images to process — relative to this script's directory
IMG_ROOT = Path(__file__).parent / "src" / "static" / "img"

# Directories (relative to IMG_ROOT) that get their own max-width rule
SUBDIR_MAX_WIDTHS: dict[str, int] = {
    "speakers": 600,
    "social_proof": 900,
    "conference_info": 1200,
}

# Directories to skip entirely
SKIP_DIRS: set[str] = {"favicon"}

# Source extensions to process
SOURCE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg"}

# Default WebP compression settings
DEFAULT_QUALITY = 80       # 75–85 is the sweet spot
DEFAULT_MAX_WIDTH = 1600   # global fallback
WEBP_METHOD = 6            # slowest / best compression (0–6)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def human_size(nbytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.1f}{unit}"
        nbytes /= 1024
    return f"{nbytes:.1f}TB"


def resize_if_needed(img: "Image.Image", max_width: int) -> "Image.Image":
    """Downscale image if it exceeds max_width, preserving aspect ratio."""
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    return img


def get_max_width(rel_path: Path, global_max: int) -> int:
    """Return the max-width rule for a given image path."""
    # rel_path is relative to IMG_ROOT, e.g. speakers/EricM_3.png → first part = "speakers"
    top_subdir = rel_path.parts[0] if len(rel_path.parts) > 1 else ""
    return SUBDIR_MAX_WIDTHS.get(top_subdir, global_max)


def convert_image(
    src_path: Path,
    quality: int,
    global_max_width: int,
    dry_run: bool,
    force: bool,
) -> bool:
    """
    Convert a single image to WebP.
    Returns True if a conversion was performed (or would be in dry-run mode).
    """
    webp_path = src_path.with_suffix(".webp")

    if webp_path.exists() and not force:
        return False  # already done, skip

    rel = src_path.relative_to(IMG_ROOT)
    max_width = get_max_width(rel, global_max_width)

    if dry_run:
        print(f"  [dry-run] Would convert: {rel}  (max_width={max_width}px, quality={quality})")
        return True

    orig_size = src_path.stat().st_size

    with Image.open(src_path) as img:
        # Preserve transparency — WebP supports alpha natively.
        # Only flatten to RGB when there is genuinely no alpha channel.
        if img.mode in ("RGBA", "LA"):
            img = img.convert("RGBA")
        elif img.mode == "PA":
            img = img.convert("RGBA")
        elif img.mode == "P":
            # Palette image: check if it carries transparency
            if "transparency" in img.info:
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
        elif img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        img = resize_if_needed(img, max_width)
        img.save(webp_path, format="WEBP", quality=quality, method=WEBP_METHOD)

    new_size = webp_path.stat().st_size
    reduction = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0

    print(
        f"  Converted: {src_path.name} → {webp_path.name}"
        f"  ({human_size(orig_size)} → {human_size(new_size)}, -{reduction:.0f}%)"
    )
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PNG/JPG images to optimized WebP using Pillow."
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        metavar="N",
        help=f"WebP quality 1–100 (default: {DEFAULT_QUALITY})",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=DEFAULT_MAX_WIDTH,
        metavar="PX",
        help=f"Global max width in pixels (default: {DEFAULT_MAX_WIDTH}). Per-directory rules in SUBDIR_MAX_WIDTHS take precedence.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be converted without writing any files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reconvert images even if a .webp file already exists.",
    )
    args = parser.parse_args()

    if not IMG_ROOT.is_dir():
        sys.exit(f"ERROR: Image directory not found: {IMG_ROOT}")

    print(f"Scanning: {IMG_ROOT}")
    print(f"Settings: quality={args.quality}, max_width={args.max_width}px, dry_run={args.dry_run}, force={args.force}\n")

    converted = 0
    skipped = 0
    errors = 0

    for root, dirs, files in os.walk(IMG_ROOT):
        root_path = Path(root)
        rel_root = root_path.relative_to(IMG_ROOT)

        # Skip excluded directories (in-place to also prevent os.walk descending)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        # Print sub-directory heading
        if rel_root != Path("."):
            print(f"[{rel_root}]")

        for filename in sorted(files):
            file_path = root_path / filename
            if file_path.suffix.lower() not in SOURCE_EXTENSIONS:
                continue

            try:
                did_convert = convert_image(
                    file_path,
                    quality=args.quality,
                    global_max_width=args.max_width,
                    dry_run=args.dry_run,
                    force=args.force,
                )
                if did_convert:
                    converted += 1
                else:
                    skipped += 1
            except Exception as exc:
                print(f"  ERROR: {filename} — {exc}")
                errors += 1

    print(f"\nDone.  Converted: {converted}  |  Skipped (already exist): {skipped}  |  Errors: {errors}")


if __name__ == "__main__":
    main()
