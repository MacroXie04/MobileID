import logging

from index.models import BarcodeUserProfile, Transaction
from index.services.usage_limit import UsageLimitService
from rest_framework import serializers

from index.models import Barcode

logger = logging.getLogger(__name__)


class BarcodeSerializer(serializers.ModelSerializer):
    """Serializer for listing barcodes"""

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

    class Meta:
        model = Barcode
        fields = [
            "id",
            "barcode_type",
            "barcode",
            "time_created",
            "share_with_others",
            "usage_count",
            "last_used",
            "display_name",
            "owner",
            "is_owned_by_current_user",
            "has_profile_addon",
            "profile_info",
            "recent_transactions",
            "usage_stats",
            "daily_usage_limit",
        ]
        read_only_fields = ["id", "barcode_type", "time_created"]

    def _get_usage(self, obj):
        """Get the first BarcodeUsage using the prefetch cache."""
        usages = obj.barcodeusage_set.all()
        return usages[0] if usages else None

    def get_usage_count(self, obj):
        """Get total usage count for the barcode

        Note: Identification barcodes will always return 0 since we don't track
        their usage (they regenerate each time). The data is still returned
        for consistency and potential admin/debugging purposes.
        """
        usage = self._get_usage(obj)
        return usage.total_usage if usage else 0

    def get_last_used(self, obj):
        """Get last used timestamp for the barcode"""
        usage = self._get_usage(obj)
        return usage.last_used if usage else None

    def get_display_name(self, obj):
        """Get display name for the barcode based on its type"""
        if obj.barcode_type == "Identification":
            return f"{obj.user.username}'s identification barcode"
        elif obj.barcode_type == "DynamicBarcode":
            return f"Dynamic Barcode ending with {obj.barcode[-4:]}"
        else:  # Others type (Static Barcode)
            return f"Barcode ending with {obj.barcode[-4:]}"

    def get_owner(self, obj):
        """Get the owner username of the barcode"""
        return obj.user.username

    def get_is_owned_by_current_user(self, obj):
        """Check if the barcode is owned by the current user"""
        request = self.context.get("request")
        if request and request.user:
            return obj.user == request.user
        return False

    def get_has_profile_addon(self, obj):
        """Return True if a BarcodeUserProfile is linked to this barcode"""
        try:
            # Reverse OneToOne relation; will raise DoesNotExist if missing
            _ = obj.barcodeuserprofile
            return True
        except BarcodeUserProfile.DoesNotExist:
            return False
        except Exception:
            logger.exception("Error checking profile addon for barcode %s", obj.pk)
            return False

    def get_profile_info(self, obj):
        """Get profile information if available"""
        try:
            profile = obj.barcodeuserprofile
            return {
                "name": profile.name,
                "information_id": profile.information_id,
                "has_avatar": bool(profile.user_profile_img),
            }
        except BarcodeUserProfile.DoesNotExist:
            return None
        except Exception:
            logger.exception("Error fetching profile info for barcode %s", obj.pk)
            return None

    def get_recent_transactions(self, obj):
        """Return last 3 transactions for this barcode."""
        try:
            if hasattr(obj, "prefetched_transactions"):
                txns = obj.prefetched_transactions[:3]
            else:
                txns = (
                    Transaction.objects.filter(barcode_used=obj)
                    .select_related("user")
                    .order_by("-time_created")[:3]
                )
            return [
                {
                    "id": t.id,
                    "user": t.user.username if t.user_id else None,
                    "time_created": t.time_created,
                }
                for t in txns
            ]
        except Exception:
            logger.exception("Error fetching transactions for barcode %s", obj.pk)
            return []

    def get_usage_stats(self, obj):
        """Get usage statistics including daily and total limits."""
        usage = self._get_usage(obj)
        if usage is None:
            return {
                "daily_used": 0,
                "daily_limit": 0,
                "total_used": 0,
                "total_limit": 0,
                "daily_remaining": None,
                "total_remaining": None,
            }

        if hasattr(obj, "prefetched_transactions"):
            start_of_day, end_of_day = UsageLimitService._today_window()
            daily_used = sum(
                1
                for t in obj.prefetched_transactions
                if t.time_created and start_of_day <= t.time_created < end_of_day
            )
        else:
            return UsageLimitService.get_usage_stats(obj)

        return {
            "daily_used": daily_used,
            "daily_limit": usage.daily_usage_limit,
            "total_used": usage.total_usage,
            "total_limit": usage.total_usage_limit,
            "daily_remaining": (
                None
                if usage.daily_usage_limit == 0
                else max(0, usage.daily_usage_limit - daily_used)
            ),
            "total_remaining": (
                None
                if usage.total_usage_limit == 0
                else max(0, usage.total_usage_limit - usage.total_usage)
            ),
        }

    def get_daily_usage_limit(self, obj):
        """Get the daily usage limit for quick access."""
        usage = self._get_usage(obj)
        return usage.daily_usage_limit if usage else 0
