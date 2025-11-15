from authn.api.keys import get_public_key
from authn.api.webauthn import (
    CookieTokenObtainPairView,
    RSALoginView,
    api_logout,
    user_info,
    api_register,
    user_img,
    api_profile,
    api_avatar_upload,
    passkey_register_options,
    passkey_register_verify,
    passkey_auth_options,
    passkey_auth_verify,
)
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

app_name = "authn"

urlpatterns = [
    # RSA public key endpoint (must be before token endpoint for proper routing)
    path("public-key/", get_public_key, name="api_public_key"),
    # JWT authentication endpoints
    path("login/", RSALoginView.as_view(), name="api_rsa_login"),  # New encrypted-only login
    path("token/", CookieTokenObtainPairView.as_view(), name="api_token_obtain_pair"),  # Legacy endpoint
    path("token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("logout/", api_logout, name="api_logout"),
    path("register/", api_register, name="api_register"),
    # user info
    path("user_info/", user_info, name="api_user_info"),
    # get user profile photo
    path("user_img/", user_img, name="api_user_image"),
    # profile management
    path("profile/", api_profile, name="api_profile"),
    path("profile/avatar/", api_avatar_upload, name="api_avatar_upload"),
    # Passkeys
    path("passkeys/register/options/", passkey_register_options, name="passkey_register_options"),
    path("passkeys/register/verify/", passkey_register_verify, name="passkey_register_verify"),
    path("passkeys/auth/options/", passkey_auth_options, name="passkey_auth_options"),
    path("passkeys/auth/verify/", passkey_auth_verify, name="passkey_auth_verify"),
]
