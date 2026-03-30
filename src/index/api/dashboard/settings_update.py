from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from index.models import UserBarcodeSettings, UserBarcodePullSettings
from index.serializers import (
    UserBarcodeSettingsSerializer,
    UserBarcodePullSettingsSerializer,
)


class DashboardSettingsUpdateMixin:
    """POST handler: update user barcode settings and/or pull settings."""

    def post(self, request):
        with transaction.atomic():
            return self._post_inner(request)

    def _post_inner(self, request):
        user = request.user
        settings, _ = UserBarcodeSettings.objects.get_or_create(user=user)

        # Create a copy of request data to potentially modify
        data = request.data.copy()
        barcode_requested = "barcode" in data

        # Track pull setting state changes
        existing_pull_settings = UserBarcodePullSettings.objects.filter(
            user=user
        ).first()
        pull_settings_enabled_before = (
            existing_pull_settings.pull_setting == "Enable"
            if existing_pull_settings
            else False
        )
        pull_settings_enabled_after = pull_settings_enabled_before

        # Handle pull_settings if provided
        pull_settings_data = data.pop("pull_settings", None)
        if pull_settings_data:
            pull_settings, _ = UserBarcodePullSettings.objects.get_or_create(user=user)
            pull_serializer = UserBarcodePullSettingsSerializer(
                pull_settings, data=pull_settings_data, partial=True
            )
            if pull_serializer.is_valid():
                pull_serializer.save()
                pull_settings.refresh_from_db()
                pull_settings_enabled_after = pull_settings.pull_setting == "Enable"
            else:
                return Response(
                    {
                        "status": "error",
                        "errors": {"pull_settings": pull_serializer.errors},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            pull_settings = existing_pull_settings

        pull_setting_enabled_now = (
            pull_settings_data is not None
            and pull_settings_enabled_after
            and not pull_settings_enabled_before
        )

        if (
            barcode_requested
            and pull_settings_enabled_after
            and not pull_setting_enabled_now
        ):
            return Response(
                {
                    "status": "error",
                    "errors": {
                        "barcode": [
                            "Barcode selection is disabled when pull setting "
                            "is enabled."
                        ]
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If pull_setting is enabled, auto-clear barcode selection
        if pull_settings_enabled_after:
            data.pop("barcode", None)  # Remove from incoming data
            if settings.barcode is not None:
                settings.barcode = None
                settings.save()

        # Let the serializer handle automatic setting of associate_user_profile_with_barcode  # noqa: E501
        # based on barcode type. No manual intervention needed here.

        serializer = UserBarcodeSettingsSerializer(
            settings, data=data, context={"request": request}, partial=True
        )

        if serializer.is_valid():
            serializer.save()

            # Get updated pull settings for response
            pull_settings, _ = UserBarcodePullSettings.objects.get_or_create(user=user)
            pull_settings_serializer = UserBarcodePullSettingsSerializer(pull_settings)

            return Response(
                {
                    "status": "success",
                    "message": "Barcode settings updated successfully",
                    "settings": serializer.data,
                    "pull_settings": pull_settings_serializer.data,
                }
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
