"""
RSA key pair utilities for fetching active keys
"""
import logging
from functools import lru_cache

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from authn.models import RSAKeyPair

logger = logging.getLogger(__name__)

# Cache key for active RSA key pair
CACHE_KEY_ACTIVE_RSA_KEY = "authn:active_rsa_keypair"
CACHE_TIMEOUT = 3600  # 1 hour


def get_active_rsa_keypair():
    """
    Get the currently active RSA key pair.

    Returns:
        RSAKeyPair: The active key pair instance

    Raises:
        ObjectDoesNotExist: If no active key pair exists
    """
    # Try cache first
    cached_key = cache.get(CACHE_KEY_ACTIVE_RSA_KEY)
    if cached_key:
        try:
            return RSAKeyPair.objects.get(pk=cached_key, is_active=True)
        except RSAKeyPair.DoesNotExist:
            # Cache is stale, clear it
            cache.delete(CACHE_KEY_ACTIVE_RSA_KEY)

    # Query database
    try:
        key_pair = RSAKeyPair.objects.get(is_active=True)
        # Cache the key ID for faster lookup
        cache.set(CACHE_KEY_ACTIVE_RSA_KEY, key_pair.pk, CACHE_TIMEOUT)
        return key_pair
    except RSAKeyPair.DoesNotExist:
        logger.error("No active RSA key pair found. Run: python manage.py generate_rsa_keypair")
        raise
    except RSAKeyPair.MultipleObjectsReturned:
        logger.error("Multiple active RSA key pairs found. This should not happen!")
        # Get the most recently created one
        key_pair = RSAKeyPair.objects.filter(is_active=True).order_by("-created_at").first()
        # Deactivate others
        RSAKeyPair.objects.filter(is_active=True).exclude(pk=key_pair.pk).update(is_active=False)
        cache.set(CACHE_KEY_ACTIVE_RSA_KEY, key_pair.pk, CACHE_TIMEOUT)
        return key_pair


def clear_rsa_keypair_cache():
    """Clear the cached active RSA key pair"""
    cache.delete(CACHE_KEY_ACTIVE_RSA_KEY)

