from index.models import Barcode, BarcodeUserProfile, Transaction
from index.services.usage_limit import UsageLimitService
from rest_framework import serializers


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

    def get_usage_count(self, obj):
        """Get total usage count for the barcode

        Note: Identification barcodes will always return 0 since we don't track
        their usage (they regenerate each time). The data is still returned
        for consistency and potential admin/debugging purposes.
        """
        try:
            return obj.barcodeusage_set.first().total_usage
        except:
            return 0

    def get_last_used(self, obj):
        """Get last used timestamp for the barcode"""
        try:
            return obj.barcodeusage_set.first().last_used
        except:
            return None

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
            return None

    def get_recent_transactions(self, obj):
        """Return last 3 transactions for this barcode."""
        try:
            qs = (
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
                for t in qs
            ]
        except Exception:
            return []

    def get_usage_stats(self, obj):
        """Get usage statistics including daily and total limits."""
        return UsageLimitService.get_usage_stats(obj)

    def get_daily_usage_limit(self, obj):
        """Get the daily usage limit for quick access."""
        try:
            usage = obj.barcodeusage_set.first()
            return usage.daily_usage_limit if usage else 0
        except:
            return 0


class BarcodeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new barcodes"""

    class Meta:
        model = Barcode
        fields = ["barcode"]

    def validate_barcode(self, value):
        """Clean and validate barcode"""
        return value.strip()

    def create(self, validated_data):
        """Create barcode with automatic type detection"""
        user = self.context["request"].user
        barcode_value = validated_data["barcode"]

        # Check if 28-digit numeric and user is in School group
        is_28_digit = len(barcode_value) == 28 and barcode_value.isdigit()
        is_school = user.groups.filter(name="School").exists()

        if is_28_digit and is_school:
            # Dynamic barcode - save only last 14 digits
            barcode_type = "DynamicBarcode"
            barcode_value = barcode_value[-14:]
        else:
            # Other barcode type
            barcode_type = "Others"

        barcode_obj = Barcode.objects.create(
            user=user, barcode=barcode_value, barcode_type=barcode_type
        )

        # Transaction creation is handled in the view/service layer
        return barcode_obj
