from rest_framework.response import Response

from index.repositories import BarcodeRepository, SettingsRepository
from index.serializers import (
    BarcodeSerializer,
    UserBarcodeSettingsSerializer,
    UserBarcodePullSettingsSerializer,
)


class DashboardRetrieveMixin:
    """GET handler: retrieve user settings and barcodes."""

    def get(self, request):
        user = request.user

        # Get or create user settings (single DynamoDB item)
        settings = SettingsRepository.get_or_create(user.id)

        # Get dashboard barcodes (user's own + shared DynamicBarcodes)
        barcodes = BarcodeRepository.get_dashboard_barcodes(user.id)

        # Extract pull settings from the merged settings item
        pull_settings_data = {
            "pull_setting": settings.get("pull_setting", "Disable"),
            "gender_setting": settings.get("pull_gender_setting", "Unknow"),
        }

        # Serialize data
        shared_context = {
            "request": request,
            "pull_settings": pull_settings_data,
            "barcodes": barcodes,
        }
        settings_serializer = UserBarcodeSettingsSerializer(
            settings, context=shared_context
        )
        pull_settings_serializer = UserBarcodePullSettingsSerializer(
            data=pull_settings_data
        )
        pull_settings_serializer.is_valid()

        barcodes_serializer = BarcodeSerializer(
            barcodes, many=True, context=shared_context
        )

        return Response(
            {
                "settings": settings_serializer.data,
                "pull_settings": pull_settings_data,
                "barcodes": barcodes_serializer.data,
            }
        )
