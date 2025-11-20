import logging

from authn.api.utils import set_auth_cookies
from authn.services.passkeys import (
    build_authentication_options,
    build_registration_options,
    verify_and_create_passkey,
    verify_authentication,
)
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from ..helpers import _clear_challenge, _get_valid_challenge, _store_challenge


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def passkey_register_options(request):
    options = build_registration_options(request.user)
    _store_challenge(request, "webauthn_reg_chal", options["challenge"])
    get_token(request)
    return Response({"success": True, "publicKey": options})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def passkey_register_verify(request):
    expected = _get_valid_challenge(request, "webauthn_reg_chal")
    if not expected:
        return Response(
            {"success": False, "message": "Missing or expired challenge"},
            status=400,
        )
    try:
        verify_and_create_passkey(request.user, request.data, expected)
        _clear_challenge(request, "webauthn_reg_chal")
        return Response({"success": True})
    except Exception as exc:
        return Response({"success": False, "message": str(exc)}, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
def passkey_auth_options(request):
    username = None
    try:
        username = request.data.get("username")
    except Exception:
        pass
    user = User.objects.filter(username=username).first() if username else None
    options = build_authentication_options(user)
    _store_challenge(request, "webauthn_auth_chal", options["challenge"])
    get_token(request)
    return Response({"success": True, "publicKey": options})


@api_view(["POST"])
@permission_classes([AllowAny])
def passkey_auth_verify(request):
    expected = _get_valid_challenge(request, "webauthn_auth_chal")
    if not expected:
        return Response(
            {"success": False, "message": "Missing or expired challenge"},
            status=400,
        )
    try:
        user = verify_authentication(request.data, expected)
    except Exception:
        logging.exception("Failed to verify passkey authentication")
        return Response(
            {"success": False, "message": "Authentication failed"}, status=400
        )

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response = Response({"success": True, "message": "Login successful"})
    set_auth_cookies(response, access_token, refresh_token, request=request)
    _clear_challenge(request, "webauthn_auth_chal")
    return response
