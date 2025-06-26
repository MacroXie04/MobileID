from rest_framework import (
    status,
    generics,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from mobileid.serializers.userprofile import UserProfileSerializer


class UserProfileAPIView(generics.RetrieveUpdateAPIView):

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # make sure to return the user instance associated with the request
        return self.request.user