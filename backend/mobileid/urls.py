from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from barcode.settings import (
    API_ENABLED,
    WEBAPP_ENABLED,
)
from mobileid.views import (
    webauthn,
    index,
    barcode,
    change_info,
)
from .api.webauthn import (
    register_view,
    current_user_view
)

app_name = "mobileid"

urlpatterns = [
    # get the server status
    # path("api/status/", status, name="status"),
]


if API_ENABLED:
    urlpatterns += [
        # webauthn api
        path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
        path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

        # user registration (username+password+student info -> token)
        path("api/register/", register_view, name="register"),

        # get current user info (token -> user info)
        path("api/current_user/", current_user_view, name="current_user"),

        # generate barcode using token
        # path("api/generate_code/", generate_code, name="generate_code"),
    ]

if WEBAPP_ENABLED:
    urlpatterns += [
        # index page
        path("", index.index, name="index"),

        # webauthn registration
        path("register/", webauthn.web_register, name="web_register"),
        # webauthn login
        path("login/", webauthn.web_login, name="web_login"),
        # webauthn logout
        path("logout/", webauthn.web_logout, name="web_logout"),

        # create barcode
        path("manage_barcode/", barcode.create_barcode, name="manage_barcode"),
        # generate barcode
        path("generate_barcode/", barcode.generate_barcode, name="generate_barcode"),
        path("barcode/delete/<int:pk>/", barcode.delete_barcode, name="delete_barcode"),

        # edit profile
        path("edit_profile/", change_info.edit_profile, name="edit_profile"),
        # edit barcode settings
        path("barcode_settings/", change_info.edit_barcode_settings, name="barcode_settings"),
    ]