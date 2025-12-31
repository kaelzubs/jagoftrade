import hashlib
import logging
from io import BytesIO
from typing import Optional, Tuple

import requests
from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

# Hard limits to protect storage and Pillow from huge images
MAX_IMAGE_PIXELS = 20_000_000  # 20 MP
MAX_DIMENSION = 4096  # 4k bounding box


def _hash_for_name(url: str, asin: str) -> str:
    h = hashlib.sha256(f"{asin}|{url}".encode("utf-8")).hexdigest()[:16]
    return h


def _normalize_image(img: Image.Image) -> Image.Image:
    # Convert to RGB; flatten alpha onto white background if present
    if img.mode in ("RGBA", "LA", "P"):
        base = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            base.paste(img, mask=img.split()[-1])
        else:
            base.paste(img)
        img = base
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Bound the dimensions while preserving aspect ratio
    w, h = img.size
    if max(w, h) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    return img


def fetch_and_prepare_image(url: str, asin: str, timeout: float = 10.0) -> Tuple[Optional[ContentFile], str]:
    """
    Downloads an image, validates content, normalizes mode, re-encodes to JPEG,
    and returns a ContentFile with a deterministic filename.
    """
    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Image download failed (%s): %s", url, exc)
        return None, ""

    content_type = resp.headers.get("Content-Type", "").lower()
    if "image" not in content_type:
        logger.warning("Rejected non-image content-type for %s: %s", url, content_type)
        return None, ""

    # Read bytes carefully to avoid huge memory usage
    raw = resp.content
    try:
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
        img = Image.open(BytesIO(raw))
        img.verify()  # quick format check
        img = Image.open(BytesIO(raw))  # reopen after verify
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("Invalid image payload for %s: %s", url, exc)
        return None, ""

    img = _normalize_image(img)

    out = BytesIO()
    try:
        img.save(out, format="JPEG", quality=85, optimize=True)
    except OSError as exc:
        logger.warning("Failed to encode image to JPEG for %s: %s", url, exc)
        return None, ""

    out.seek(0)
    content_file = ContentFile(out.getvalue())

    suffix = _hash_for_name(url, asin)
    filename = f"{asin}_{suffix}.jpg"
    return content_file, filename