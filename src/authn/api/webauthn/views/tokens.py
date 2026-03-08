import logging

from authn.api.utils import clear_auth_cookies, set_auth_cookies
from authn.throttling import (
    LoginRateThrottle,
    RefreshRateThrottle,
    UsernameRateThrottle,
)
from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from ..serializers import (
    EncryptedTokenObtainPairSerializer,
    RSAEncryptedLoginSerializer,
)

logger = logging.getLogger(__name__)


def _ensure_outstanding_token(refresh_token_str):
    """
    Ensure the refresh token is tracked in OutstandingToken table.
    This is needed for device management functionality.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        token = RefreshToken(refresh_token_str)
        jti = token.get("jti")
        user_id = token.get("user_id")

        # Check if already exists
        if not OutstandingToken.objects.filter(jti=jti).exists():
            user = User.objects.get(id=user_id)
            OutstandingToken.objects.create(
                user=user,
                jti=jti,
                token=str(token),
                created_at=token.current_time,
                expires_at=token.current_time + token.lifetime,
            )
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning(
            "Failed to ensure outstanding token: %s", exc, exc_info=True
        )


if getattr(settings, "THROTTLES_ENABLED", True):
    LOGIN_VIEW_THROTTLES = (LoginRateThrottle, UsernameRateThrottle)
else:
    LOGIN_VIEW_THROTTLES = ()


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_scope = "login"
    serializer_class = EncryptedTokenObtainPairSerializer
    throttle_classes = LOGIN_VIEW_THROTTLES + tuple(
        api_settings.DEFAULT_THROTTLE_CLASSES
    )

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access = response.data.get("access")
            refresh = response.data.get("refresh")
            if access and refresh:
                set_auth_cookies(response, access, refresh, request=request)
                # Force CSRF cookie to be set/rotated so frontend can read it
                get_token(request)
                # Track the refresh token for device management
                _ensure_outstanding_token(refresh)
                if not settings.AUTH_EXPOSE_TOKENS_IN_BODY:
                    response.data.pop("access", None)
                    response.data.pop("refresh", None)
        return response


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [RefreshRateThrottle]

    def post(self, request, *args, **kwargs):
        # Check if refresh token is in cookies but not in body
        refresh_missing = "refresh" not in request.data
        cookie_has_refresh = "refresh_token" in request.COOKIES
        if refresh_missing and cookie_has_refresh:
            data = request.data.copy()
            data["refresh"] = request.COOKIES["refresh_token"]

            serializer = self.get_serializer(data=data)
            try:
                serializer.is_valid(raise_exception=True)
            except TokenError as e:
                raise InvalidToken(e.args[0])

            response = Response(serializer.validated_data, status=200)
        else:
            # Refresh token is in request body
            # Ensure we have the refresh field
            if "refresh" not in request.data:
                return Response(
                    {"detail": "Refresh token is required"},
                    status=400,
                )
            try:
                response = super().post(request, *args, **kwargs)
            except InvalidToken:
                # Handle invalid token errors
                # Optionally log via logging if desired
                return Response({"detail": "Invalid token."}, status=400)

        if response.status_code == 200:
            access = response.data.get("access")
            refresh = response.data.get("refresh")
            if access and refresh:
                set_auth_cookies(response, access, refresh, request=request)
                # Force CSRF cookie to be set/rotated so frontend can read it
                get_token(request)
                if settings.AUTH_EXPOSE_TOKENS_IN_BODY:
                    # Ensure response body contains tokens (super() may strip them)
                    if "access" not in response.data or "refresh" not in response.data:
                        response.data = {
                            "access": access,
                            "refresh": refresh,
                        }
                else:
                    response.data.pop("access", None)
                    response.data.pop("refresh", None)
        return response


@api_view(["POST"])
def api_logout(request):
    # Best-effort blacklist of the refresh token (if present)
    try:
        rt = request.COOKIES.get("refresh_token")
        if rt:
            RefreshToken(rt).blacklist()
    except Exception:
        logger.warning("Failed to blacklist refresh token during logout", exc_info=True)

    resp = Response({"message": "Logged out"})
    return clear_auth_cookies(resp)


class RSALoginView(TokenObtainPairView):
    """
    Login view that ENFORCES RSA-encrypted password submissions.
    This is the new secure login endpoint that requires encrypted passwords
    with nonce.
    """

    permission_classes = [AllowAny]
    throttle_scope = "login"
    serializer_class = RSAEncryptedLoginSerializer
    throttle_classes = LOGIN_VIEW_THROTTLES + tuple(
        api_settings.DEFAULT_THROTTLE_CLASSES
    )

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access = response.data.get("access")
            refresh = response.data.get("refresh")
            if access and refresh:
                set_auth_cookies(response, access, refresh, request=request)
                # Track the refresh token for device management
                _ensure_outstanding_token(refresh)
                data = {"message": "Login successful"}
                if settings.AUTH_EXPOSE_TOKENS_IN_BODY:
                    data["access"] = access
                    data["refresh"] = refresh
                response.data = data
        return response
