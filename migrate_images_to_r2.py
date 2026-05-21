#!/usr/bin/env python3
"""One-time migration: upload src/static/img/ to Cloudflare R2 and update the DB.

Usage
-----
    # Dry run — shows what would be uploaded and which DB rows would change.
    python migrate_images_to_r2.py --dry-run

    # Real run — uploads files, updates DB, then prompts before deleting locals.
    python migrate_images_to_r2.py

    # Skip the deletion prompt (for CI / heroku run one-offs).
    python migrate_images_to_r2.py --delete-local

Required env vars (set in .env or Heroku config)
--------------------------------------------------
    R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME, R2_PUBLIC_URL

What it does
------------
1. Validates all R2 env vars are present.
2. Walks src/static/img/ recursively.
3. For each file:
   - If NOT already .webp AND file size > 1 MB  →  convert to WebP in memory,
     upload under the .webp key.
   - Otherwise  →  upload as-is, keeping the original filename/extension.
4. Opens a Flask app context and updates every affected DB column to the new
   full CDN URL.
5. Optionally deletes src/static/img/ to shrink the Heroku slug.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
IMG_ROOT = REPO_ROOT / "src" / "static" / "img"

# Load .env before importing Flask app (so DATABASE_URL etc are available).
from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Migrate static/img to Cloudflare R2")
parser.add_argument("--dry-run", action="store_true", help="Print actions without uploading or changing the DB")
parser.add_argument("--delete-local", action="store_true", help="Delete local img files after migration without prompting")
args = parser.parse_args()

DRY_RUN = args.dry_run
AUTO_DELETE = args.delete_local

# ---------------------------------------------------------------------------
# Preflight: check R2 env vars
# ---------------------------------------------------------------------------
from src.services.r2 import is_configured, upload_bytes, r2_url, _require_var

if not is_configured():
    print("\n❌  R2 is not fully configured. Set these environment variables:")
    for v in ("R2_ENDPOINT_URL", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME", "R2_PUBLIC_URL"):
        from os import getenv
        status = "✓" if getenv(v, "").strip() else "✗ MISSING"
        print(f"   {status}  {v}")
    sys.exit(1)

R2_PUBLIC_URL = _require_var("R2_PUBLIC_URL").rstrip("/")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
SUPPORTED_CONVERT = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".tiff", ".tif", ".bmp"}
ONE_MB = 1 * 1024 * 1024  # 1 MiB

MIME_MAP = {
    ".webp": "image/webp",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".svg":  "image/svg+xml",
    ".tiff": "image/tiff",
    ".tif":  "image/tiff",
    ".bmp":  "image/bmp",
    ".avif": "image/avif",
    ".ico":  "image/x-icon",
}


def _mime(path: Path) -> str:
    return MIME_MAP.get(path.suffix.lower(), "application/octet-stream")


def _build_r2_key(local_path: Path, override_stem: str | None = None) -> str:
    """Return the R2 key for a file.  Mirrors the local structure under img/."""
    rel = local_path.relative_to(IMG_ROOT)
    parts = list(rel.parts)
    if override_stem:
        parts[-1] = override_stem
    return "img/" + "/".join(parts)


# ---------------------------------------------------------------------------
# Phase 1: upload files
# ---------------------------------------------------------------------------
print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Scanning {IMG_ROOT} …\n")

# key_map: local_path -> uploaded CDN URL
# Used in Phase 2 to update DB rows.
key_map: dict[str, str] = {}   # str(local_path) -> cdn_url

uploaded = 0
converted = 0
skipped = 0
errors = 0

for local_path in sorted(IMG_ROOT.rglob("*")):
    if not local_path.is_file():
        continue

    suffix = local_path.suffix.lower()
    rel = local_path.relative_to(REPO_ROOT / "src" / "static")  # e.g. img/speakers/foo.webp
    size = local_path.stat().st_size

    # Decide whether to convert/recompress to WebP (any raster >1 MB)
    should_convert = (suffix in SUPPORTED_CONVERT) and (size > ONE_MB)

    if should_convert:
        r2_stem = local_path.stem + ".webp"
        r2_key = _build_r2_key(local_path, override_stem=r2_stem)
        verb = "RECOMPRESS+UPLOAD" if suffix == ".webp" else "CONVERT+UPLOAD"
        action = f"{verb} ({size / 1024:.0f} KB  →  webp)"
        converted += 1
    else:
        r2_key = _build_r2_key(local_path)
        action = f"UPLOAD ({size / 1024:.0f} KB)"

    cdn_url = f"{R2_PUBLIC_URL}/{r2_key}"
    print(f"  {action}\n    {rel}  →  {r2_key}")

    if not DRY_RUN:
        try:
            raw = local_path.read_bytes()
            if should_convert:
                from src.services.image_optimizer import convert_bytes_to_webp
                raw, _ = convert_bytes_to_webp(raw, local_path.name, force=suffix == ".webp")
                mime = "image/webp"
            else:
                mime = _mime(local_path)
            cdn_url = upload_bytes(raw, r2_key, mime)
            uploaded += 1
        except Exception as exc:
            print(f"    ⚠  FAILED: {exc}")
            errors += 1
            continue

    # Record the mapping using both path styles templates might store
    local_abs = str(local_path)
    key_map[local_abs] = cdn_url

    # Also record by relative paths used in DB columns:
    # e.g. "img/speakers/foo.webp"  or  "/static/img/speakers/foo.webp"
    static_rel = str(rel)                        # img/speakers/foo.webp
    static_slash = f"/static/{static_rel}"       # /static/img/speakers/foo.webp

    key_map[static_rel]   = cdn_url
    key_map[static_slash] = cdn_url

    # If a conversion happened, the old filename in the DB is the pre-webp name
    if should_convert:
        old_rel   = str(rel.parent / local_path.name)             # img/.../foo.jpg
        old_slash = f"/static/{old_rel}"                           # /static/img/.../foo.jpg
        key_map[old_rel]   = cdn_url
        key_map[old_slash] = cdn_url

print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Summary: {uploaded} uploaded, {converted} converted, {errors} errors\n")

if errors and not DRY_RUN:
    print("⚠  Aborting DB update due to upload errors. Fix failures and re-run.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Phase 2: update DB
# ---------------------------------------------------------------------------
print(f"{'[DRY RUN] ' if DRY_RUN else ''}Updating database …\n")

from run import app

db_rows_updated = 0

with app.app_context():
    from src.models.main import (
        db,
        Speaker, Artist, Sponsor, Church,
        Video, Podcast, SocialProof,
    )

    def _map(val: str | None) -> str | None:
        if not val:
            return None
        return key_map.get(val) or key_map.get(val.lstrip("/"))

    # --- Single-column models ---
    for Model, col in [
        (Speaker,  "image"),
        (Artist,   "image"),
        (Sponsor,  "logo_url"),
        (Church,   "logo_url"),
        (Video,    "thumbnail_mobile"),
        (Podcast,  "thumbnail_mobile"),
    ]:
        rows = Model.query.all()
        for row in rows:
            old_val = getattr(row, col, None)
            new_val = _map(old_val)
            if new_val and new_val != old_val:
                print(f"  {Model.__tablename__}.{col} id={row.id}: {old_val!r}\n    → {new_val!r}")
                if not DRY_RUN:
                    setattr(row, col, new_val)
                    db_rows_updated += 1

    # --- SocialProof.img_json (JSON array of strings) ---
    for row in SocialProof.query.all():
        imgs = json.loads(row.img_json) if row.img_json else []
        new_imgs = []
        changed = False
        for url in imgs:
            mapped = _map(url)
            if mapped and mapped != url:
                new_imgs.append(mapped)
                changed = True
                print(f"  social_proof.img_json id={row.id}: {url!r}\n    → {mapped!r}")
            else:
                new_imgs.append(url)
        if changed:
            if not DRY_RUN:
                row.img_json = json.dumps(new_imgs)
                db_rows_updated += 1

    if not DRY_RUN:
        db.session.commit()
        print(f"\n✓  Committed {db_rows_updated} DB row updates.\n")
    else:
        print(f"\n[DRY RUN] Would update {db_rows_updated} DB rows.\n")

# ---------------------------------------------------------------------------
# Phase 3: optionally delete local img files
# ---------------------------------------------------------------------------
if DRY_RUN:
    print("[DRY RUN] Local files NOT deleted. Re-run without --dry-run to migrate.\n")
    sys.exit(0)

if AUTO_DELETE:
    do_delete = True
else:
    answer = input(f"Delete local {IMG_ROOT} directory? This CANNOT be undone. [y/N] ").strip().lower()
    do_delete = answer == "y"

if do_delete:
    shutil.rmtree(IMG_ROOT)
    print(f"✓  Deleted {IMG_ROOT}\n")
else:
    print("Local files kept. You can delete them manually once you've verified R2.\n")

print("Migration complete ✓\n")
