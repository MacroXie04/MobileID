from django.db.models import Prefetch, Q
from rest_framework.response import Response

from index.models import (
    Barcode,
    Transaction,
    UserBarcodeSettings,
    UserBarcodePullSettings,
)
from index.serializers import (
    BarcodeSerializer,
    UserBarcodeSettingsSerializer,
    UserBarcodePullSettingsSerializer,
)


class DashboardRetrieveMixin:
    """GET handler: retrieve user settings and barcodes."""

    def get(self, request):
        user = request.user

        # Get or create user settings
        settings, created = UserBarcodeSettings.objects.get_or_create(
            user=user,
            defaults={
                "barcode": None,
                "associate_user_profile_with_barcode": False,
                "scanner_detection_enabled": False,
                "prefer_front_camera": True,
            },
        )

        # All users see shared DynamicBarcodes + own barcodes
        barcodes = (
            Barcode.objects.filter(
                (
                    Q(barcode_type="DynamicBarcode")
                    & (Q(user=user) | Q(share_with_others=True))
                )
                | Q(
                    user=user,
                    barcode_type__in=["Others", "Identification"],
                )
            )
            .select_related("user")
            .prefetch_related(
                "barcodeuserprofile",
                "barcodeusage_set",
                Prefetch(
                    "transaction_set",
                    queryset=Transaction.objects.select_related("user").order_by(
                        "-time_created"
                    ),
                    to_attr="prefetched_transactions",
                ),
            )
            .order_by("-time_created")
        )

        # Get or create pull settings
        pull_settings, _ = UserBarcodePullSettings.objects.get_or_create(
            user=user,
            defaults={"pull_setting": "Disable", "gender_setting": "Unknow"},
        )

        # Serialize data
        shared_context = {
            "request": request,
            "pull_settings": pull_settings,
            "barcodes": barcodes,
        }
        settings_serializer = UserBarcodeSettingsSerializer(
            settings, context=shared_context
        )
        pull_settings_serializer = UserBarcodePullSettingsSerializer(pull_settings)
        barcodes_serializer = BarcodeSerializer(
            barcodes, many=True, context=shared_context
        )

        return Response(
            {
                "settings": settings_serializer.data,
                "pull_settings": pull_settings_serializer.data,
                "barcodes": barcodes_serializer.data,
            }
        )
