"""Cloudflare R2 object-storage helper.

All interaction with R2 goes through this module.  The bucket is accessed
via the S3-compatible API using boto3.

Required environment variables
--------------------------------
R2_ENDPOINT_URL        https://<account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID       R2 API token key ID
R2_SECRET_ACCESS_KEY   R2 API token secret
R2_BUCKET_NAME         Name of the R2 bucket
R2_PUBLIC_URL          Public base URL, e.g. https://pub-xxx.r2.dev  (no trailing slash)

Public helpers
--------------
upload_bytes(data, key, content_type)  -> str   full CDN URL
delete_key(key)                        -> None
r2_url(key)                            -> str   CDN URL without uploading
is_configured()                        -> bool  True when all env vars are set
"""

from __future__ import annotations

import logging
from functools import lru_cache
from os import getenv
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import boto3 as _boto3_type

logger = logging.getLogger(__name__)

_REQUIRED_VARS = (
    "R2_ENDPOINT_URL",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_NAME",
    "R2_PUBLIC_URL",
)


def is_configured() -> bool:
    """Return True only when every required env var is set and non-empty."""
    return all(getenv(v, "").strip() for v in _REQUIRED_VARS)


def _require_var(name: str) -> str:
    value = getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"R2 is not configured: environment variable {name!r} is missing or empty. "
            f"Set all of: {', '.join(_REQUIRED_VARS)}"
        )
    return value


@lru_cache(maxsize=1)
def _client():
    """Return a lazily-constructed, cached boto3 S3 client for R2."""
    import boto3

    endpoint = _require_var("R2_ENDPOINT_URL")
    key_id = _require_var("R2_ACCESS_KEY_ID")
    secret = _require_var("R2_SECRET_ACCESS_KEY")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
        region_name="auto",  # R2 accepts "auto" and ignores it
    )


def upload_bytes(data: bytes, key: str, content_type: str) -> str:
    """Upload *data* to the bucket at *key* and return the full public CDN URL.

    Sets a one-year Cache-Control header so CDN edge nodes cache aggressively.
    The key should be a forward-slash path, e.g. ``img/speakers/foo.webp``.
    """
    bucket = _require_var("R2_BUCKET_NAME")
    public_url = _require_var("R2_PUBLIC_URL").rstrip("/")

    _client().put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        CacheControl="public, max-age=31536000, immutable",
    )

    cdn_url = f"{public_url}/{key}"
    logger.info("R2 upload OK: %s → %s", key, cdn_url)
    return cdn_url


def delete_key(key: str) -> None:
    """Delete *key* from the bucket.  Silently ignores 'key not found' errors."""
    bucket = _require_var("R2_BUCKET_NAME")
    try:
        _client().delete_object(Bucket=bucket, Key=key)
        logger.info("R2 delete OK: %s", key)
    except Exception as exc:
        logger.warning("R2 delete failed for %s: %s", key, exc)


def r2_url(key: str) -> str:
    """Build the public CDN URL for *key* without any network call."""
    public_url = _require_var("R2_PUBLIC_URL").rstrip("/")
    return f"{public_url}/{key}"
