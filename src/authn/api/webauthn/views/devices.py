"""
Device management API views.

Provides endpoints for listing, viewing, and revoking user sessions/devices.
Uses simplejwt's OutstandingToken model to track active refresh tokens,
combined with LoginAuditLog for device metadata.
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import UntypedToken

from authn.models import AccessTokenBlacklist, LoginAuditLog


def _get_current_session_iat(request):
    """
    Get the 'iat' (issued-at) timestamp of the current session from the access token.

    Since access tokens and refresh tokens are created together, they share the
    same 'iat'. We use this to match the current session with OutstandingToken
    records.

    Returns None if no valid iat is found.
    """
    # Get the validated access token from the authentication
    # The request.auth contains the validated token if authentication succeeded
    if hasattr(request, "auth") and request.auth:
        return request.auth.get("iat")
    return None


def _get_current_refresh_token_jti(request):
    """
    Extract the JTI (JWT ID) to identify the current device/session.

    This is used when revoking sessions to prevent self-revocation.
    We use a combination of methods to identify the current session.

    Returns None if no valid JTI is found.
    """
    # Priority 1: Get JTI directly from request body
    if hasattr(request, "data") and request.data:
        current_jti = request.data.get("current_jti")
        if current_jti and isinstance(current_jti, str) and len(current_jti) > 0:
            return current_jti

    # Priority 2: Try to extract JTI from refresh_token cookie
    refresh_token = request.COOKIES.get("refresh_token")
    if refresh_token:
        try:
            token = UntypedToken(refresh_token)
            return token.get("jti")
        except (InvalidToken, TokenError):
            pass

    return None


def _parse_device_info(user_agent):
    """
    Parse User-Agent string to extract readable device/browser information.
    Returns a dict with device_name, browser, os, and device_type.
    """
    if not user_agent:
        return {
            "device_name": "Unknown Device",
            "browser": "Unknown",
            "os": "Unknown",
            "device_type": "unknown",
        }

    ua_lower = user_agent.lower()

    # Detect OS
    if "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"
        device_type = "mobile" if "iphone" in ua_lower else "tablet"
    elif "android" in ua_lower:
        os_name = "Android"
        device_type = "mobile" if "mobile" in ua_lower else "tablet"
    elif "macintosh" in ua_lower or "mac os" in ua_lower:
        os_name = "macOS"
        device_type = "desktop"
    elif "windows" in ua_lower:
        os_name = "Windows"
        device_type = "desktop"
    elif "linux" in ua_lower:
        os_name = "Linux"
        device_type = "desktop"
    elif "cros" in ua_lower:
        os_name = "Chrome OS"
        device_type = "desktop"
    else:
        os_name = "Unknown"
        device_type = "unknown"

    # Detect Browser
    if "edg/" in ua_lower or "edge/" in ua_lower:
        browser = "Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    elif "chrome" in ua_lower and "safari" in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
    elif "msie" in ua_lower or "trident" in ua_lower:
        browser = "Internet Explorer"
    else:
        browser = "Unknown Browser"

    device_name = f"{browser} on {os_name}"

    return {
        "device_name": device_name,
        "browser": browser,
        "os": os_name,
        "device_type": device_type,
    }


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
        # We use a time window approach: first look for an audit within ±5 seconds,
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
    from datetime import timedelta

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
