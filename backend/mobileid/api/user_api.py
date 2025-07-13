from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from mobileid.models import UserBarcodeSettings
from mobileid.serializers.userprofile import (UserBarcodeSettingsSerializer,
                                              UserProfileSerializer)
from mobileid.throttling import UserProfileRateThrottle


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserProfileRateThrottle]

    def get_object(self):
        # make sure to return the user instance associated with the request
        return self.request.user


class BarcodeSettingsAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserBarcodeSettingsSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserProfileRateThrottle]

    def get_object(self):
        settings, created = UserBarcodeSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings
