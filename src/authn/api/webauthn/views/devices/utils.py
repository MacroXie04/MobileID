"""
Shared helpers for device/session management endpoints.
"""

from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken


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
