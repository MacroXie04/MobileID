from django.urls import path

from authn.api.webauthn import CookieTokenObtainPairView, api_logout, user_info, api_register
from authn.api.manage import user_profile_api, upload_avatar_api

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
    
    # User profile management endpoints
    path("profile/", user_profile_api, name="api_user_profile"),
    path("profile/avatar/", upload_avatar_api, name="api_upload_avatar"),
]
