from authn.api.utils import clear_auth_cookies, set_auth_cookies
from authn.throttling import LoginRateThrottle, UsernameRateThrottle
from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ..serializers import (
    EncryptedTokenObtainPairSerializer,
    RSAEncryptedLoginSerializer,
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
        return response


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Check if refresh token is in cookies but not in body
        if "refresh" not in request.data and "refresh_token" in request.COOKIES:
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
                    {"detail": "Refresh token is required"}, status=400
                )
            try:
                response = super().post(request, *args, **kwargs)
            except InvalidToken as e:
                # Handle invalid token errors
                # Optionally log the exception info here using logging (not shown)
                return Response(
                    {"detail": "Invalid token."}, status=400
                )

        # Ensure tokens are returned in response body (for localStorage usage)
        if response.status_code == 200:
            access = response.data.get("access")
            refresh = response.data.get("refresh")
            if access and refresh:
                set_auth_cookies(response, access, refresh, request=request)
                # Force CSRF cookie to be set/rotated so frontend can read it
                get_token(request)
                # Ensure response body contains tokens (may have been modified by super())
                if "access" not in response.data or "refresh" not in response.data:
                    response.data = {
                        "access": access,
                        "refresh": refresh,
                    }
        return response


@api_view(["POST"])
def api_logout(request):
    # Best-effort blacklist of the refresh token (if present)
    try:
        rt = request.COOKIES.get("refresh_token")
        if rt:
            try:
                RefreshToken(rt).blacklist()
            except Exception:
                pass
    except Exception:
        pass

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
                response.data = {
                    "message": "Login successful",
                    "access": access,
                    "refresh": refresh,
                }
        return response
