from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from mobileid.serializers.webauthn import RegisterSerializer
from mobileid.throttling import RegistrationRateThrottle


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_classes = [RegistrationRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # do not return token, because user is not active
        response_data = serializer.data
        response_data['message'] = 'Registration successful!'
        response_data['is_active'] = False

        headers = self.get_success_headers(serializer.data)

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
