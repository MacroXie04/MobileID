from .forms import UserRegisterForm
from .views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LoginView,
    api_avatar_upload,
    api_logout,
    api_profile,
    api_register,
    list_devices,
    revoke_all_other_devices,
    revoke_device,
    csrf_token,
    user_img,
    user_info,
)

__all__ = [
    "CookieTokenObtainPairView",
    "CookieTokenRefreshView",
    "LoginView",
    "api_avatar_upload",
    "api_logout",
    "api_profile",
    "api_register",
    "list_devices",
    "revoke_all_other_devices",
    "revoke_device",
    "csrf_token",
    "UserRegisterForm",
    "user_img",
    "user_info",
]
