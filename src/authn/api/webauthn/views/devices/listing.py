"""
Device listing API views.
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from authn.models import LoginAuditLog

from .utils import _get_current_session_iat, _parse_device_info


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_devices(request):
    """
    List all active devices/sessions for the current user.

    Returns a list of devices with:
    - id: Token ID for revocation
    - device_name: Human-readable device description
    - browser: Browser name
    - os: Operating system
    - device_type: desktop/mobile/tablet/unknown
    - ip_address: Last known IP address
    - created_at: When the session was created (login time)
    - expires_at: When the session will expire (next re-login required)
    - last_active: Last activity time (from audit log)
    - is_current: Whether this is the current device
    """
    # Get the current session's iat from the access token
    # This is more reliable than matching JTI since access/refresh tokens share iat
    current_iat = _get_current_session_iat(request)

    # Get all non-blacklisted, non-expired tokens for the user
    now = timezone.now()
    tokens = (
        OutstandingToken.objects.filter(
            user=request.user,
            expires_at__gt=now,  # Only include non-expired tokens
        )
        .exclude(id__in=BlacklistedToken.objects.values_list("token_id", flat=True))
        .order_by("-created_at")
    )

    devices = []
    for token in tokens:
        # Find the closest successful login audit log entry to the token creation time.
        # We use a time window approach: first look for an audit within +/-5 seconds,
        # then fallback to just before the token if nothing found.
        # This prevents matching the wrong session when multiple logins occur.
        time_window = timedelta(seconds=5)
        window_start = token.created_at - time_window
        window_end = token.created_at + time_window

        # First, try to find an audit log within the time window around token creation
        audit = (
            LoginAuditLog.objects.filter(
                user=request.user,
                success=True,
                created_at__gte=window_start,
                created_at__lte=window_end,
            )
            .order_by("-created_at")
            .first()
        )

        # Fallback: if no audit in the tight window, find the closest one before token
        # This handles edge cases where audit logging was slightly delayed
        if audit is None:
            audit = (
                LoginAuditLog.objects.filter(
                    user=request.user,
                    success=True,
                    created_at__lte=token.created_at,
                )
                .order_by("-created_at")
                .first()
            )

        # Parse device info from user agent
        user_agent = audit.user_agent if audit else ""
        device_info = _parse_device_info(user_agent)

        # Check if this is the current session by comparing iat timestamps
        # Access token and refresh token share the same iat when created together
        token_iat = int(token.created_at.timestamp())
        is_current = current_iat is not None and abs(token_iat - int(current_iat)) <= 2

        devices.append(
            {
                "id": token.id,
                "jti": token.jti,
                "device_name": device_info["device_name"],
                "browser": device_info["browser"],
                "os": device_info["os"],
                "device_type": device_info["device_type"],
                "ip_address": audit.ip_address if audit else None,
                "user_agent": user_agent,
                "created_at": token.created_at.isoformat(),
                "expires_at": token.expires_at.isoformat(),
                "last_active": audit.created_at.isoformat() if audit else None,
                "is_current": is_current,
            }
        )

    return Response({"devices": devices, "count": len(devices)})
