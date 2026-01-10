import logging

from authn.services.login_challenge import issue_login_challenge
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def login_challenge(request):
    try:
        payload = issue_login_challenge()
    except Exception as e:
        # Log error without full traceback for expected configuration issues
        logger.error(
            "Failed to issue login challenge: %s. Run: python manage.py "
            "generate_rsa_keypair",
            str(e),
        )
        return Response(
            {
                "detail": "No active RSA key pair available. Please run the "
                "key generation command."
            },
            status=503,
        )
    get_token(request)
    return Response(payload)


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_token(request):
    """
    Lightweight endpoint to issue a CSRF cookie for SPA clients.
    """
    token = get_token(request)
    return Response({"csrfToken": token})
