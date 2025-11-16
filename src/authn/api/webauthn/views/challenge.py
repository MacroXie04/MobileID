import logging

from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from authn.services.login_challenge import issue_login_challenge

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def login_challenge(request):
    try:
        payload = issue_login_challenge()
    except Exception:
        logger.exception("Failed to issue login challenge")
        return Response(
            {"detail": "No active RSA key pair available. Please run the key generation command."},
            status=503,
        )
    get_token(request)
    return Response(payload)

