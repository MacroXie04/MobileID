from django.urls import path

from authn.views import (webauthn, index, change_info)

from barcode.settings import (API_SERVER)

from authn.api.webauthn import CookieTokenObtainPairView, api_logout, user_info

from rest_framework_simplejwt.views import TokenRefreshView

app_name = "authn"

urlpatterns = []

if API_SERVER:
    urlpatterns += [
        # JWT authentication endpoints
        path("token/", CookieTokenObtainPairView.as_view(), name="api_token_obtain_pair"),
        path("token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
        path("logout/", api_logout, name="api_logout"),
        path("user_info/", user_info, name="api_user_info"),
    ]

else:
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
