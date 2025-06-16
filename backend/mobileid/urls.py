from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import webauthn

app_name = "mobileid"

urlpatterns = [
    # 登录接口（用户名+密码 -> token）
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # 当前用户信息（需要 Authorization: Bearer <access>）
    path('api/me/', webauthn.current_user_view),
]