from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from mobileid.serializers.webauthn import RegisterSerializer


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    # 我们将重写整个 create 方法以完全控制流程
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ----- 核心修复点在这里 -----
        # 1. 调用 serializer.save()，它会返回被创建的 user 实例
        #    这个实例来自于我们之前在 serializer.create() 方法中返回的 user 对象
        user = serializer.save()

        # 2. 现在 user 是一个真正的 User model 实例，可以用来生成 token
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        # 3. 准备返回给前端的数据
        #    我们使用 serializer.data 来获取用户基本信息（不含密码）
        #    然后将 tokens 合并进去
        response_data = serializer.data
        response_data['tokens'] = tokens

        headers = self.get_success_headers(serializer.data)

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
