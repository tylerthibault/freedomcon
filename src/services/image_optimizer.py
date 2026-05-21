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

SUPPORTED_INPUT = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".tiff", ".tif", ".bmp"}


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


def convert_bytes_to_webp(
    data: bytes,
    filename: str,
    quality: int = 80,
    max_width: int | None = None,
    force: bool = False,
) -> tuple[bytes, str]:
    """Convert raw image bytes to WebP entirely in memory.

    Applies the same EXIF transpose, resize, and RGBA/RGB handling as
    ``convert_to_webp``.  No files are read from or written to disk.

    Parameters
    ----------
    data:      Raw bytes of the source image.
    filename:  Original filename, used only to detect the source extension
               (e.g. ``"logo.png"`` → lossless WebP; ``"photo.jpg"`` → lossy).
    quality:   WebP quality for lossy encoding (1-100, default 80).
    max_width: If set, resize the image so its width does not exceed this value.

    Returns
    -------
    (webp_bytes, new_filename)  where *new_filename* has the ``.webp`` extension.

    Raises
    ------
    ValueError   if the file extension is not supported.
    RuntimeError if Pillow fails to open or encode the image.
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".webp" and not force:
        # Already WebP — return as-is with the original filename.
        webp_name = Path(filename).stem + ".webp"
        return data, webp_name

    if suffix not in SUPPORTED_INPUT:
        raise ValueError(f"Unsupported image type: {suffix!r}")

    webp_name = Path(filename).stem + ".webp"

    try:
        with Image.open(io.BytesIO(data)) as image:
            prepared = _prepare(image, max_width)
            webp_bytes = _encode_webp(prepared, suffix, quality=quality)
    except Exception as exc:
        raise RuntimeError(f"Failed to convert {filename!r} to WebP: {exc}") from exc

    return webp_bytes, webp_name


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
