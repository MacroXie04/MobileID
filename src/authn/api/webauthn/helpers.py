import base64
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

PASSKEY_CHALLENGE_TTL_SECONDS = getattr(
    settings, "PASSKEY_CHALLENGE_TTL_SECONDS", 300
)


def _clean_base64(b64: str) -> str:
    """
    Remove any data-URI prefix and return the raw Base64.
    """
    if b64.startswith("data:image"):
        b64 = b64.split(",", 1)[1]
    return b64.strip()


def _b64_any_to_bytes(data: str) -> bytes:
    """
    Decode Base64 in a robust way:
    - Accept both standard and URL-safe Base64
    - Auto-fix missing padding
    """
    if not isinstance(data, str):
        raise ValueError("Invalid base64 data")
    s = data.strip().replace("-", "+").replace("_", "/")
    # Add padding to multiple of 4
    pad = (-len(s)) % 4
    if pad:
        s += "=" * pad
    return base64.b64decode(s)


def _store_challenge(request, key: str, challenge: str):
    request.session[key] = challenge
    expires_at = timezone.now() + timedelta(
        seconds=PASSKEY_CHALLENGE_TTL_SECONDS
    )
    request.session[f"{key}_expires_at"] = expires_at.timestamp()
    request.session.modified = True


def _get_valid_challenge(request, key: str):
    challenge = request.session.get(key)
    expires_at = request.session.get(f"{key}_expires_at")
    if not challenge or expires_at is None:
        return None
    if timezone.now().timestamp() > expires_at:
        _clear_challenge(request, key)
        return None
    return challenge


def _clear_challenge(request, key: str):
    request.session.pop(key, None)
    request.session.pop(f"{key}_expires_at", None)
    request.session.modified = True
