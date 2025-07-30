from django.urls import path

from authn.api.webauthn import CookieTokenObtainPairView, api_logout, user_info, api_register, user_img, api_profile, api_avatar_upload
from authn.api.passkeys import (
    passkey_registration_options,
    passkey_registration_verify,
    passkey_authentication_options,
    passkey_authentication_verify,
    passkey_list,
    passkey_delete
)

from rest_framework_simplejwt.views import TokenRefreshView

app_name = "authn"

urlpatterns = [
    # JWT authentication endpoints
    path("token/", CookieTokenObtainPairView.as_view(), name="api_token_obtain_pair"),
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
    
    # Passkey endpoints
    path("passkeys/register/options/", passkey_registration_options, name="passkey_registration_options"),
    path("passkeys/register/verify/", passkey_registration_verify, name="passkey_registration_verify"),
    path("passkeys/authenticate/options/", passkey_authentication_options, name="passkey_authentication_options"),
    path("passkeys/authenticate/verify/", passkey_authentication_verify, name="passkey_authentication_verify"),
    path("passkeys/", passkey_list, name="passkey_list"),
    path("passkeys/<int:passkey_id>/", passkey_delete, name="passkey_delete"),
]
