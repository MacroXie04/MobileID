from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from views.webauthn import current_user_view

urlpatterns = [
    # 登录接口（用户名+密码 -> token）
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # 当前用户信息（需要 Authorization: Bearer <access>）
    path('api/me/', current_user_view),
]