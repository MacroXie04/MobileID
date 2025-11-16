from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from authn.api.utils import clear_auth_cookies, set_auth_cookies
from authn.throttling import LoginRateThrottle, UsernameRateThrottle

from ..serializers import EncryptedTokenObtainPairSerializer, RSAEncryptedLoginSerializer

LOGIN_VIEW_THROTTLES = (LoginRateThrottle, UsernameRateThrottle)


class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_scope = "login"
    serializer_class = EncryptedTokenObtainPairSerializer
    throttle_classes = LOGIN_VIEW_THROTTLES + tuple(api_settings.DEFAULT_THROTTLE_CLASSES)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access = response.data.get("access")
            refresh = response.data.get("refresh")
            if access and refresh:
                set_auth_cookies(response, access, refresh, request=request)
        return response


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access = response.data.get("access")
            refresh = response.data.get("refresh")
            if access and refresh:
                set_auth_cookies(response, access, refresh, request=request)
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
    This is the new secure login endpoint that requires encrypted passwords with nonce.
    """

    permission_classes = [AllowAny]
    throttle_scope = "login"
    serializer_class = RSAEncryptedLoginSerializer
    throttle_classes = LOGIN_VIEW_THROTTLES + tuple(api_settings.DEFAULT_THROTTLE_CLASSES)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access = response.data.get("access")
            refresh = response.data.get("refresh")
            if access and refresh:
                set_auth_cookies(response, access, refresh, request=request)
                response.data = {"message": "Login successful"}
        return response

