import logging

from rest_framework import serializers

from index.repositories import TransactionRepository
from index.services.usage_limit import UsageLimitService

logger = logging.getLogger(__name__)


class BarcodeSerializer(serializers.Serializer):
    """Serializer for listing barcodes (DynamoDB-backed)."""

    barcode_uuid = serializers.CharField(read_only=True)
    barcode_type = serializers.CharField(read_only=True)
    barcode = serializers.CharField(read_only=True)
    time_created = serializers.CharField(read_only=True)
    share_with_others = serializers.BooleanField(read_only=True)
    usage_count = serializers.SerializerMethodField()
    last_used = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_owned_by_current_user = serializers.SerializerMethodField()
    has_profile_addon = serializers.SerializerMethodField()
    profile_info = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    usage_stats = serializers.SerializerMethodField()
    daily_usage_limit = serializers.SerializerMethodField()

    def get_usage_count(self, obj):
        return int(obj.get("total_usage", 0))

    def get_last_used(self, obj):
        return obj.get("last_used")

    def get_display_name(self, obj):
        barcode_type = obj.get("barcode_type")
        barcode_val = obj.get("barcode", "")
        if barcode_type == "DynamicBarcode":
            return f"Dynamic Barcode ending with {barcode_val[-4:]}"
        return f"Barcode ending with {barcode_val[-4:]}"

    def get_owner(self, obj):
        return obj.get("owner_username", "Unknown")

    def get_is_owned_by_current_user(self, obj):
        request = self.context.get("request")
        if request and request.user:
            return obj.get("user_id") == str(request.user.id)
        return False

    def get_has_profile_addon(self, obj):
        return bool(obj.get("profile_name"))

    def get_profile_info(self, obj):
        if not obj.get("profile_name"):
            return None
        return {
            "name": obj.get("profile_name"),
            "information_id": obj.get("profile_info_id"),
            "has_avatar": bool(obj.get("profile_avatar")),
        }

    def get_recent_transactions(self, obj):
        try:
            txns = TransactionRepository.for_barcode(
                barcode_uuid=obj["barcode_uuid"],
                limit=3,
            )
            return [
                {
                    "id": t["sk"],
                    "user": t.get("user_id"),
                    "time_created": t.get("time_created"),
                }
                for t in txns
            ]
        except Exception:
            logger.exception(
                "Error fetching transactions for barcode %s",
                obj.get("barcode_uuid"),
            )
            return []

    def get_usage_stats(self, obj):
        return UsageLimitService.get_usage_stats(obj)

    def get_daily_usage_limit(self, obj):
        return int(obj.get("daily_usage_limit", 0))
