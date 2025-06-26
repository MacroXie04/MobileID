from django.contrib.auth import login
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import LoginSerializer



class LoginView(APIView):
    """
    处理用户登录的视图。
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # 将请求数据和上下文（包含request对象）传递给序列化器
        serializer = LoginSerializer(data=request.data, context={'request': request})

        # 运行验证，如果失败，raise_exception=True 会自动抛出异常
        # DRF 会捕获此异常并返回一个标准的 400 Bad Request 响应，其中包含错误详情
        serializer.is_valid(raise_exception=True)

        # 从验证过的数据中获取 user 对象
        user = serializer.validated_data['user']

        # 使用 Django 的 login 函数创建 session
        login(request, user)

        # 返回成功的响应
        # 你可以根据需要返回更多用户信息，但 "detail" 已足够
        return Response({"detail": "登录成功。"}, status=status.HTTP_200_OK)