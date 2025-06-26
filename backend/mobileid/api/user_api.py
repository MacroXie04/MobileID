from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from mobileid.serializers.userprofile import UserProfileSerializer


class UserProfileAPIView(APIView):
    """
    API endpoint to retrieve the authenticated user's profile information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
