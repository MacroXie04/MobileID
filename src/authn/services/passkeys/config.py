from typing import List
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _rp_id() -> str:
    # Require RP ID or derive strictly from BACKEND_ORIGIN (no localhost
    # fallback)
    rp = getattr(settings, "WEBAUTHN_RP_ID", None)
    if rp:
        return rp
    backend_origin = getattr(settings, "BACKEND_ORIGIN", None)
    if not backend_origin:
        raise ImproperlyConfigured(
            "WEBAUTHN_RP_ID or BACKEND_ORIGIN must be set in environment"
        )
    parsed = urlparse(backend_origin)
    host = parsed.hostname
    if not host:
        raise ImproperlyConfigured(
            "BACKEND_ORIGIN must include a valid hostname (e.g., "
            "https://example.com)"
        )
    return host


def _origins() -> List[str]:
    allowed: List[str] = []
    backend = getattr(settings, "BACKEND_ORIGIN", None)
    if backend:
        allowed.append(backend)
    frontends = getattr(settings, "FRONTEND_ORIGINS", []) or []
    allowed.extend(frontends)

    # Normalize (strip trailing slash). Do not inject any localhost variants.
    normalized: List[str] = []
    for origin in allowed:
        if not origin:
            continue
        normalized.append(origin.rstrip("/"))

    if not normalized:
        raise ImproperlyConfigured(
            "BACKEND_ORIGIN or FRONTEND_ORIGINS must be set in environment"
        )

    # De-dup and sort for stable output
    return sorted(set(normalized))
