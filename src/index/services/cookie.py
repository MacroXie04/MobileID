"""Cookie processing service

This module provides a scaffold for normalizing and validating user-supplied
CatCard cookies before they are used by downstream services.

Fill in the TODOs where indicated to implement your project-specific logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ProcessedCookie:
    """Normalized cookie container used by downstream flows."""

    # Raw header-ready cookie string (e.g., "a=1; b=2")
    header_value: str

    # Optional: parsed key/value view for convenience
    kv: Dict[str, str]

    # Optional: any warnings encountered during processing
    warnings: Tuple[str, ...] = ()


def _parse_cookie_to_kv(raw_cookie: str) -> Dict[str, str]:
    """Parse a Cookie header string into a dict of key/value pairs.

    NOTE: This is a minimal, permissive parser. Replace as needed.
    """
    pairs: Dict[str, str] = {}
    for part in (raw_cookie or "").split(";"):
        if not part.strip():
            continue
        if "=" not in part:
            # Skip attributes that aren't k=v
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k:
            pairs[k] = v
    return pairs


def process_user_cookie(raw_cookie: str) -> ProcessedCookie:
    """Normalize and validate the user-provided CatCard cookie.

    - Trims whitespace
    - Validates required session cookies (session_for%3Aindex_php)
    - Filters out tracking/analytics cookies to reduce header size
    - Returns a header-ready cookie string and filtered key-value pairs
    - Provides warnings for missing required cookies

    Args:
        raw_cookie: The raw cookie string from the user

    Returns:
        ProcessedCookie with filtered cookies and any validation warnings
    """
    if raw_cookie is None:
        raw_cookie = ""

    cookie = raw_cookie.strip()

    # Basic parse for inspection
    kv = _parse_cookie_to_kv(cookie)

    warnings = []

    # Enforce presence of required CatCard session keys
    required_keys = [
        "session_for%3Aindex_php",  # Main CatCard session key (URL encoded)
    ]
    for key in required_keys:
        if key not in kv or not kv[key].strip():
            warnings.append(f"Missing required cookie key: {key}")

    # Remove known tracking/analytics keys that are unnecessary
    # and may bloat headers or cause issues.
    blacklist_prefixes = [
        "_ga",
        "_fbp",
        "_tt",
        "_pk_",
        "_scid",
        "_uetvid",
        "nmstat",
        "_mkto",
    ]
    filtered_kv = {
        k: v
        for k, v in kv.items()
        if not any(k.startswith(prefix) for prefix in blacklist_prefixes)
    }

    # Additional validation: check if we have at least one session-related
    # cookie
    session_keys = [k for k in filtered_kv.keys() if "session" in k.lower()]
    if not session_keys:
        warnings.append("No session cookies found - authentication may fail")

    # Rebuild the header_value from filtered cookies
    header_value = (
        "; ".join(f"{k}={v}" for k, v in filtered_kv.items()) if filtered_kv else ""
    )

    return ProcessedCookie(
        header_value=header_value, kv=filtered_kv, warnings=tuple(warnings)
    )
