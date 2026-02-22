from authn.api.keys import get_public_key
from authn.api.webauthn import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    RSALoginView,
    api_logout,
    list_devices,
    revoke_all_other_devices,
    revoke_device,
    login_challenge,
    csrf_token,
    user_info,
    api_register,
    user_img,
    api_profile,
    api_avatar_upload,
)
from django.urls import path

app_name = "authn"

urlpatterns = [
    # RSA public key endpoint (must be before token endpoint for proper
    # routing)
    path("public-key/", get_public_key, name="api_public_key"),
    path("csrf/", csrf_token, name="api_csrf_token"),
    # JWT authentication endpoints
    path("login-challenge/", login_challenge, name="api_login_challenge"),
    path(
        "login/", RSALoginView.as_view(), name="api_rsa_login"
    ),  # New encrypted-only login
    path(
        "token/",
        CookieTokenObtainPairView.as_view(),
        name="api_token_obtain_pair",
    ),  # Legacy endpoint
    path(
        "token/refresh/",
        CookieTokenRefreshView.as_view(),
        name="api_token_refresh",
    ),
    path("logout/", api_logout, name="api_logout"),
    path("register/", api_register, name="api_register"),
    # user info
    path("user_info/", user_info, name="api_user_info"),
    # get user profile photo
    path("user_img/", user_img, name="api_user_image"),
    # profile management
    path("profile/", api_profile, name="api_profile"),
    path("profile/avatar/", api_avatar_upload, name="api_avatar_upload"),
    # Device management
    path("devices/", list_devices, name="api_devices_list"),
    path(
        "devices/<int:token_id>/revoke/",
        revoke_device,
        name="api_device_revoke",
    ),
    path(
        "devices/revoke-all/",
        revoke_all_other_devices,
        name="api_devices_revoke_all",
    ),
]
