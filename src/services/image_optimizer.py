"""Image conversion utility — converts an uploaded image to WebP in-place.

Extracted from the local `imgopt` CLI tool. Converts any supported image file
(jpg, png, gif, bmp, tiff) to a .webp file, deletes the original, and returns
the new file path.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

SUPPORTED_INPUT = {".png", ".jpg", ".jpeg", ".gif", ".tiff", ".tif", ".bmp"}


def _has_alpha(image: Image.Image) -> bool:
    if image.mode in ("RGBA", "LA"):
        return True
    if image.mode == "P" and "transparency" in image.info:
        return True
    return False


def _prepare(image: Image.Image, max_width: int | None = None) -> Image.Image:
    """Transpose EXIF, optionally resize, convert to RGBA or RGB."""
    if getattr(image, "is_animated", False):
        image.seek(0)
    prepared = ImageOps.exif_transpose(image).copy()
    if max_width and prepared.width > max_width:
        ratio = max_width / float(prepared.width)
        new_height = max(1, round(prepared.height * ratio))
        prepared.thumbnail((max_width, new_height), Image.Resampling.LANCZOS)

    alpha = _has_alpha(prepared)
    if alpha:
        return prepared.convert("RGBA")

    if prepared.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", prepared.convert("RGBA").size, (255, 255, 255))
        bg.paste(prepared.convert("RGBA"), mask=prepared.convert("RGBA").split()[-1])
        return bg

    return prepared.convert("RGB")


def _encode_webp(image: Image.Image, source_suffix: str, quality: int = 80) -> bytes:
    """Encode image as WebP bytes. Uses lossless for PNGs with alpha."""
    alpha = _has_alpha(image)
    buf = io.BytesIO()
    if source_suffix == ".png" and alpha:
        image.save(buf, "WEBP", lossless=True, method=6)
    else:
        image.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()


def convert_to_webp(file_path: str | Path, quality: int = 80, max_width: int | None = None) -> Path:
    """Convert *file_path* to WebP in the same directory.

    - Saves the new .webp file next to the original.
    - Deletes the original file (unless it was already a .webp).
    - Returns the Path of the new .webp file.

    Raises ValueError if the file extension is not a supported input type.
    Raises RuntimeError if conversion fails.
    """
    src = Path(file_path)
    suffix = src.suffix.lower()

    # Already a webp — nothing to do
    if suffix == ".webp":
        return src

    if suffix not in SUPPORTED_INPUT:
        raise ValueError(f"Unsupported image type: {suffix}")

    dest = src.with_suffix(".webp")

    try:
        with Image.open(src) as image:
            prepared = _prepare(image, max_width)
            data = _encode_webp(prepared, suffix, quality=quality)
        dest.write_bytes(data)
    except Exception as exc:
        raise RuntimeError(f"Failed to convert {src.name} to WebP: {exc}") from exc

    # Remove original only after successful write
    src.unlink()
    return dest
