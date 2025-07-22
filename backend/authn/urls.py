from django.urls import path

from authn.views import (webauthn, index, change_info)

from barcode.settings import (API_SERVER)

from authn.api.webauthn import CookieTokenObtainPairView, api_logout, user_info, api_register
from authn.api.manage import user_profile_api, upload_avatar_api

from rest_framework_simplejwt.views import TokenRefreshView

app_name = "authn"

urlpatterns = []

# API endpoints - 使用 api/ 前缀以避免与Web路由冲突
urlpatterns += [
    # JWT authentication endpoints
    path("api/token/", CookieTokenObtainPairView.as_view(), name="api_token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("api/logout/", api_logout, name="api_logout"),
    path("api/user_info/", user_info, name="api_user_info"),
    path("api/register/", api_register, name="api_register"),
    
    # User profile management endpoints
    path("api/profile/", user_profile_api, name="api_user_profile"),
    path("api/profile/avatar/", upload_avatar_api, name="api_upload_avatar"),
]

# Web endpoints - 只在非纯API模式下启用
if not API_SERVER:
    urlpatterns += [
        # staff index page
        path("", index.staff_index, name="web_staff_index"),

        # edit profile
        path("edit_profile/", change_info.edit_profile, name="web_edit_profile"),

        # webauthn
        path("login/", webauthn.web_login, name="web_login"),
        path("logout/", webauthn.web_logout, name="web_logout"),
        path("register/", webauthn.web_register, name="web_register"),
    ]
