from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from mobileid.models import StudentInformation
from .serializers import (
    RegisterSerializer,
    CurrentUserSerializer,
    StudentInformationSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"detail": "Registered"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    user = request.user
    try:
        student_info = user.studentinformation
    except StudentInformation.DoesNotExist:
        return Response(
            {"detail": "Student profile not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    data = {
        "username": user.username,
        "email": user.email or "",
        **StudentInformationSerializer(student_info).data,
    }
    return Response(CurrentUserSerializer(data).data)
