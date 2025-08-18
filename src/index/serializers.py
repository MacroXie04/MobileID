from index.models import Barcode, UserBarcodeSettings, BarcodeUsage, BarcodeUserProfile
from rest_framework import serializers


class BarcodeSerializer(serializers.ModelSerializer):
    """Serializer for listing barcodes"""

    usage_count = serializers.SerializerMethodField()
    last_used = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_owned_by_current_user = serializers.SerializerMethodField()
    has_profile_addon = serializers.SerializerMethodField()

    class Meta:
        model = Barcode
        fields = [
            "id",
            "barcode_type",
            "barcode",
            "time_created",
            "usage_count",
            "last_used",
            "display_name",
            "owner",
            "is_owned_by_current_user",
            "has_profile_addon",
        ]
        read_only_fields = ["id", "barcode_type", "time_created"]

    def get_usage_count(self, obj):
        """Get total usage count for the barcode"""
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
        request = self.context.get('request')
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

        return Barcode.objects.create(
            user=user, barcode=barcode_value, barcode_type=barcode_type
        )


class UserBarcodeSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user barcode settings"""

    barcode_choices = serializers.SerializerMethodField()
    field_states = serializers.SerializerMethodField()

    class Meta:
        model = UserBarcodeSettings
        fields = [
            "barcode",
            "associate_user_profile_with_barcode",
            "server_verification",
            "barcode_choices",
            "field_states",
        ]

    def get_barcode_choices(self, obj):
        """Get available barcode choices for the user
        
        For School type users:
        - All dynamic barcodes (regardless of owner)
        - Their own identification barcodes
        - Their own other type barcodes
        
        For other users:
        - Only their own barcodes
        """
        user = self.context["request"].user
        is_school = user.groups.filter(name="School").exists()
        choices = []

        if is_school:
            # For School users: get all dynamic barcodes
            all_dynamic_barcodes = Barcode.objects.filter(
                barcode_type="DynamicBarcode"
            ).select_related('user').order_by("-time_created")
            
            # Add all dynamic barcodes
            for b in all_dynamic_barcodes:
                owner_name = b.user.username if b.user != user else "Your"
                display = f"{owner_name} Dynamic Barcode ending with {b.barcode[-4:]}"
                choices.append({
                    "id": b.id,
                    "display": display,
                    "barcode": b.barcode,
                    "barcode_type": b.barcode_type,
                    "full_display": f"{b.barcode_type} - {b.barcode} (Owner: {b.user.username})",
                })
            
            # Get user's own identification and other barcodes
            own_other_barcodes = Barcode.objects.filter(
                user=user,
                barcode_type__in=["Identification", "Others"]
            ).order_by("-time_created")
            
            for b in own_other_barcodes:
                if b.barcode_type == "Identification":
                    display = f"{user.username}'s identification barcode"
                else:  # Others type
                    display = f"Your Barcode ending with {b.barcode[-4:]}"
                    
                choices.append({
                    "id": b.id,
                    "display": display,
                    "barcode": b.barcode,
                    "barcode_type": b.barcode_type,
                    "full_display": f"{b.barcode_type} - {b.barcode}",
                })
        else:
            # Check if user is in User group - they only get identification barcode
            is_user = user.groups.filter(name="User").exists()
            
            if is_user:
                # User type only sees identification barcode
                barcodes = Barcode.objects.filter(
                    user=user,
                    barcode_type="Identification"
                ).order_by("-time_created")
            else:
                # Other non-School users see all their own barcodes
                barcodes = Barcode.objects.filter(user=user).order_by("-time_created")
            
            for b in barcodes:
                if b.barcode_type == "Identification":
                    display = f"{user.username}'s identification barcode"
                elif b.barcode_type == "DynamicBarcode":
                    display = f"Dynamic Barcode ending with {b.barcode[-4:]}"
                else:  # Others type
                    display = f"Barcode ending with {b.barcode[-4:]}"

                choices.append({
                    "id": b.id,
                    "display": display,
                    "barcode": b.barcode,
                    "barcode_type": b.barcode_type,
                    "full_display": f"{b.barcode_type} - {b.barcode}",
                })

        return choices

    def get_field_states(self, obj):
        """Get field states based on user group and current settings"""
        user = self.context["request"].user
        is_user_group = user.groups.filter(name="User").exists()

        return {
            "associate_user_profile_disabled": is_user_group,  # Disabled for User group only
            "barcode_disabled": False,  # Barcode selection is always enabled
        }

    def validate(self, data):
        """Simple validation based on user group only"""
        user = self.context["request"].user
        is_user_group = user.groups.filter(name="User").exists()

        # Standard users cannot enable profile association
        if is_user_group and data.get("associate_user_profile_with_barcode", False):
            raise serializers.ValidationError(
                {"associate_user_profile_with_barcode": "Standard users cannot enable profile association."}
            )

        return data
