from django.urls import path
from .api.webauthn import register_view, current_user_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = "mobileid"

urlpatterns = [
    # webauthn
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # user registration (username+password+student info -> token)
    path("register/", register_view, name="register"),

    # get current user info (token -> user info)
    path("current_user/", current_user_view, name="current_user"),
]