"""
API endpoints for RSA public key distribution
"""

import logging

from authn.models import RSAKeyPair
from authn.utils.keys import get_active_rsa_keypair
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_public_key(request):
    """
    Get the active RSA public key for password encryption.

    Returns:
        Response with JSON containing:
        - kid: Key identifier (UUID)
        - algorithm: "RSA-OAEP" or "RSA-PKCS1" (for JSEncrypt compatibility)
        - key_size: Key size in bits (2048 or 4096)
        - public_key: PEM-encoded public key

    Caching:
        - Public key is cached for 1 hour
        - Cache-Control header set appropriately
    """
    cache_key = "authn:public_key_response"
    cached_response = cache.get(cache_key)

    if cached_response:
        response = Response(cached_response)
        response["Cache-Control"] = "public, max-age=3600"
        return response

    try:
        key_pair = get_active_rsa_keypair()
    except RSAKeyPair.DoesNotExist:
        logger.error("No active RSA key pair available")
        return Response(
            {
                "detail": "No active RSA key pair available. Please run: python manage.py generate_rsa_keypair"
            },
            status=503,  # Service Unavailable
        )

    response_data = {
        "kid": str(key_pair.kid),
        "algorithm": "RSA-PKCS1",  # JSEncrypt uses PKCS1 padding
        "key_size": key_pair.key_size,
        "public_key": key_pair.public_key,
    }

    # Cache the response for 1 hour
    cache.set(cache_key, response_data, 3600)

    response = Response(response_data)
    response["Cache-Control"] = "public, max-age=3600"
    return response
