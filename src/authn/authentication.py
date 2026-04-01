import logging

from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from authn.repositories import SecurityRepository
from authn.session_revocation import SESSION_REVOCATION_MATCH_WINDOW_SECONDS

logger = logging.getLogger(__name__)


def allow_all_users_rule(user):
    """Allow inactive (pending activation) users to obtain tokens."""
    return user is not None


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
            header_token = request.META.get("HTTP_X_CSRFTOKEN", "")

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
            if jti and SecurityRepository.is_blacklisted(jti):
                logger.warning("Rejecting blacklisted token JTI: %s...", jti[:8])
                raise exceptions.AuthenticationFailed("Session has been revoked")

            user = self.get_user(validated_token)

            # Check if session has been revoked by matching user + token time.
            iat = validated_token.get("iat")
            if user and iat:
                token_iat = int(iat)
                if SecurityRepository.check_session_revocation(
                    user.id, token_iat, SESSION_REVOCATION_MATCH_WINDOW_SECONDS
                ):
                    logger.info("Rejecting revoked session for user %s", user.id)
                    raise exceptions.AuthenticationFailed(
                        "Session has been revoked. Please log in again."
                    )

        except (InvalidToken, TokenError):
            return None

        if used_cookie and request.method not in SAFE_METHODS:
            self.enforce_csrf(django_request)

        return user, validated_token
