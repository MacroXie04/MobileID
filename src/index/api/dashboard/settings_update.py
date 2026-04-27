from rest_framework import status
from rest_framework.response import Response

from index.repositories import SettingsRepository
from index.serializers import (
    UserBarcodeSettingsSerializer,
    UserBarcodePullSettingsSerializer,
)


class DashboardSettingsUpdateMixin:
    """POST handler: update user barcode settings and/or pull settings."""

    def post(self, request):
        user = request.user
        settings = SettingsRepository.get_or_create(user.id)

        data = request.data.copy()
        barcode_requested = "barcode" in data

        pull_settings_enabled_before = settings.get("pull_setting") == "Enable"
        pull_settings_enabled_after = pull_settings_enabled_before

        # Handle pull_settings if provided
        pull_settings_data = data.pop("pull_settings", None)
        if pull_settings_data:
            pull_serializer = UserBarcodePullSettingsSerializer(data=pull_settings_data)
            if pull_serializer.is_valid():
                validated = pull_serializer.validated_data
                SettingsRepository.update(
                    user.id,
                    pull_setting=validated.get(
                        "pull_setting", settings.get("pull_setting")
                    ),
                    pull_gender_setting=validated.get(
                        "gender_setting", settings.get("pull_gender_setting")
                    ),
                )
                # Refresh settings
                settings = SettingsRepository.get_or_create(user.id)
                pull_settings_enabled_after = settings.get("pull_setting") == "Enable"
            else:
                return Response(
                    {
                        "status": "error",
                        "errors": {"pull_settings": pull_serializer.errors},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
            data.pop("barcode", None)
            if settings.get("active_barcode_uuid"):
                SettingsRepository.set_active_barcode(user.id, None)
                settings["active_barcode_uuid"] = None

        # Build pull_settings dict for serializer context
        pull_settings_dict = {
            "pull_setting": settings.get("pull_setting", "Disable"),
            "gender_setting": settings.get("pull_gender_setting", "Unknow"),
        }

        serializer = UserBarcodeSettingsSerializer(
            settings,
            data=data,
            context={"request": request, "pull_settings": pull_settings_dict},
            partial=True,
        )

        if serializer.is_valid():
            validated = serializer.validated_data
            updates = {}
            if "active_barcode_uuid" in validated:
                updates["active_barcode_uuid"] = validated["active_barcode_uuid"]
                updates["active_barcode_owner_id"] = (
                    validated.get("active_barcode_owner_id", str(user.id))
                    if validated["active_barcode_uuid"]
                    else None
                )
            if "associate_user_profile_with_barcode" in validated:
                updates["associate_user_profile_with_barcode"] = validated[
                    "associate_user_profile_with_barcode"
                ]
            if "scanner_detection_enabled" in validated:
                updates["scanner_detection_enabled"] = validated[
                    "scanner_detection_enabled"
                ]
            if "prefer_front_camera" in validated:
                updates["prefer_front_camera"] = validated["prefer_front_camera"]

            if updates:
                SettingsRepository.update(user.id, **updates)

            # Refresh for response
            settings = SettingsRepository.get_or_create(user.id)

            response_settings = UserBarcodeSettingsSerializer(
                settings,
                context={"request": request, "pull_settings": pull_settings_dict},
            )

            return Response(
                {
                    "status": "success",
                    "message": "Barcode settings updated successfully",
                    "settings": response_settings.data,
                    "pull_settings": pull_settings_dict,
                }
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
