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
    settings_error,
    webauthn,
    index,
)
from .api.generate_barcode import generate_code
from .api.webauthn import (
    register_view,
    current_user_view
)

app_name = "mobileid"

urlpatterns = []

if not WEBAPP_ENABLED and not API_ENABLED:
    urlpatterns = [
        path("", settings_error.settings_error, name="settings_error"),
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
        path("api/generate_code/", generate_code, name="generate_code"),
    ]

if WEBAPP_ENABLED:
    urlpatterns += [
        # webauthn registration
        path("register/", webauthn.web_register, name="web_register"),
        # webauthn login
        path("login/", webauthn.web_login, name="web_login"),
        # webauthn logout
        path("logout/", webauthn.web_logout, name="web_logout"),

        # index page
        path("", index.index, name="index"),
    ]