"""
Device revocation API views.
"""

from datetime import timedelta

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from authn.models import AccessTokenBlacklist

from .utils import _get_current_session_iat


def _blacklist_session_access_tokens(user, session_created_at):
    """
    Blacklist access tokens associated with a session.

    Since access tokens don't directly reference their refresh token,
    we use the session creation timestamp as a session identifier.
    When checking access tokens, we compare their iat (issued-at) with
    stored revoked session timestamps.

    This enables immediate session termination when a device is revoked.
    """
    from django.conf import settings

    # Calculate access token expiry time
    access_lifetime = getattr(settings, "SIMPLE_JWT", {}).get(
        "ACCESS_TOKEN_LIFETIME", timedelta(days=1)
    )

    # Blacklist entry expires when the access token would have expired
    expires_at = session_created_at + access_lifetime

    # Create session key using timestamp - matches the JWT's iat claim
    session_ts = int(session_created_at.timestamp())
    session_key = f"session_{user.id}_{session_ts}"

    # Create a blacklist entry using session creation time as identifier
    AccessTokenBlacklist.objects.get_or_create(
        jti=session_key,
        defaults={
            "user": user,
            "expires_at": expires_at,
        },
    )


@api_view(["DELETE", "POST"])
@permission_classes([IsAuthenticated])
def revoke_device(request, token_id):
    """
    Revoke a specific device/session by blacklisting its tokens.

    This revokes both:
    1. The refresh token (prevents token refresh)
    2. Associated access tokens (immediate session termination)

    Cannot revoke the current device's token.
    """
    current_iat = _get_current_session_iat(request)

    try:
        token = OutstandingToken.objects.get(id=token_id, user=request.user)
    except OutstandingToken.DoesNotExist:
        return Response(
            {"error": "Device not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Prevent revoking current session (compare iat timestamps)
    token_iat = int(token.created_at.timestamp())
    if current_iat is not None and abs(token_iat - int(current_iat)) <= 2:
        return Response(
            {"error": "Cannot revoke current device session"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if already blacklisted
    if BlacklistedToken.objects.filter(token=token).exists():
        return Response(
            {"error": "Device already revoked"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Blacklist the refresh token
    BlacklistedToken.objects.create(token=token)

    # Also blacklist associated access tokens for immediate effect
    _blacklist_session_access_tokens(request.user, token.created_at)

    return Response({"message": "Device logged out successfully"})


@api_view(["DELETE", "POST"])
@permission_classes([IsAuthenticated])
def revoke_all_other_devices(request):
    """
    Revoke all other devices/sessions except the current one.

    Blacklists all tokens for the user except the current session's token.
    Both refresh and access tokens are revoked for immediate effect.
    """
    current_iat = _get_current_session_iat(request)

    # Get all non-blacklisted tokens for the user
    tokens = OutstandingToken.objects.filter(
        user=request.user,
    ).exclude(id__in=BlacklistedToken.objects.values_list("token_id", flat=True))

    revoked_count = 0
    for token in tokens:
        # Skip current session (compare iat timestamps)
        token_iat = int(token.created_at.timestamp())
        if current_iat is not None and abs(token_iat - int(current_iat)) <= 2:
            continue

        # Blacklist the refresh token
        BlacklistedToken.objects.create(token=token)

        # Also blacklist associated access tokens for immediate effect
        _blacklist_session_access_tokens(request.user, token.created_at)

        revoked_count += 1

    return Response(
        {
            "message": f"Successfully logged out {revoked_count} other device(s)",
            "revoked_count": revoked_count,
            "success": True,
        }
    )
