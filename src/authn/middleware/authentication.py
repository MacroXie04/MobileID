import logging

from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from authn.models import AccessTokenBlacklist

logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that supports:
    1. Token from Authorization header (standard)
    2. Token from access_token cookie (for browser-based apps)
    3. Access token blacklist checking (for immediate session revocation)
    """

    def enforce_csrf(self, request):
        check = CSRFCheck(lambda req: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            # Debugging: log the token details
            header_token = request.META.get("HTTP_X_CSRFTOKEN", "")
            print(
                f"CSRF DEBUG: Reason='{reason}'. Token='{header_token}' "
                f"(len={len(header_token)})"
            )

            # If token is "null" or "undefined" (common frontend issues),
            # provide clearer error
            if header_token in ("null", "undefined", ""):
                raise exceptions.PermissionDenied(
                    f"CSRF Failed: Token missing or invalid ({header_token}). "
                    "Please refresh the page."
                )

            raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")

    def authenticate(self, request):
        django_request = getattr(request, "_request", request)
        header = self.get_header(request)
        used_cookie = False
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = None

        if raw_token is None:
            raw_token = django_request.COOKIES.get("access_token")
            used_cookie = raw_token is not None

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)

            # Check if this access token has been blacklisted (session revoked)
            jti = validated_token.get("jti")
            if jti and AccessTokenBlacklist.is_blacklisted(jti):
                # Token has been revoked - raise authentication error
                logger.warning(f"Rejecting blacklisted token JTI: {jti}")
                raise exceptions.AuthenticationFailed("Session has been revoked")

            user = self.get_user(validated_token)

            # Check if session has been revoked by matching user + token time
            iat = validated_token.get("iat")
            if user and iat:
                token_iat = int(iat)

                # Check all revoked sessions for this user
                revoked_sessions = AccessTokenBlacklist.objects.filter(
                    user=user, jti__startswith=f"session_{user.id}_"
                )

                for entry in revoked_sessions:
                    try:
                        # Extract timestamp from session key:
                        # session_{user_id}_{timestamp}
                        stored_ts = int(entry.jti.split("_")[-1])
                        diff = abs(stored_ts - token_iat)
                        # Allow 10-second window for timestamp matching
                        if diff <= 10:
                            logger.info(f"Rejecting revoked session for user {user.id}")
                            raise exceptions.AuthenticationFailed(
                                "Session has been revoked. Please log in again."
                            )
                    except (ValueError, IndexError):
                        continue

        except (InvalidToken, TokenError):
            return None

        if used_cookie and request.method not in SAFE_METHODS:
            # TODO: Re-enable CSRF check once frontend cookie handling is fixed
            self.enforce_csrf(django_request)
            pass

        return user, validated_token
