# your_app/serializers.py

from django.contrib.auth import authenticate
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """
    处理用户登录请求的序列化器。
    """
    username = serializers.CharField(
        label="Username",
        write_only=True
    )
    password = serializers.CharField(
        label="Password",
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )

    def validate(self, attrs):
        """
        重写 validate 方法，在此处进行身份验证。
        """
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:
            msg = 'Must provide "username" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        # 使用 Django 内置的 authenticate 方法进行验证
        # 传入 request 对象是一个好习惯
        request = self.context.get('request')
        user = authenticate(request=request, username=username, password=password)

        if not user:
            msg = 'Unable to log in with provided credentials.'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs