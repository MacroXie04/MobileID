import secrets
from typing import Dict

from authn.utils.keys import get_active_rsa_keypair
from django.conf import settings
from django.core.cache import cache

CHALLENGE_CACHE_PREFIX = "authn:login_challenge:"
CHALLENGE_TTL = getattr(settings, "LOGIN_CHALLENGE_TTL_SECONDS", 120)
NONCE_BYTES = max(8, getattr(settings, "LOGIN_CHALLENGE_NONCE_BYTES", 16))


def _cache_key(nonce: str) -> str:
    return f"{CHALLENGE_CACHE_PREFIX}{nonce}"


def _generate_nonce() -> str:
    return secrets.token_hex(NONCE_BYTES)


def issue_login_challenge() -> Dict[str, str]:
    """
    Issue a one-time nonce tied to the active RSA key pair.
    """

    key_pair = get_active_rsa_keypair()
    nonce = _generate_nonce()
    cache.set(_cache_key(nonce), {"kid": str(key_pair.kid)}, CHALLENGE_TTL)

    return {
        "nonce": nonce,
        "kid": str(key_pair.kid),
        "public_key": key_pair.public_key,
        "key_size": key_pair.key_size,
        "algorithm": "RSA-OAEP",
        "expires_in": CHALLENGE_TTL,
    }


def consume_login_challenge(nonce: str) -> Dict[str, str]:
    """
    Validate and consume a previously issued nonce.
    """

    if not nonce or not isinstance(nonce, str):
        raise ValueError("Missing login challenge nonce")

    cache_key = _cache_key(nonce)
    payload = cache.get(cache_key)
    if not payload:
        raise ValueError("Invalid or expired login challenge nonce")

    cache.delete(cache_key)
    return payload
