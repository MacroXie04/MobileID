from index.models import (
    Barcode,
    UserBarcodeSettings,
    UserBarcodePullSettings,
)
from rest_framework import serializers


class UserBarcodePullSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user barcode pull settings"""

    class Meta:
        model = UserBarcodePullSettings
        fields = [
            "pull_setting",
            "gender_setting",
        ]


class UserBarcodeSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user barcode settings"""

    barcode_choices = serializers.SerializerMethodField()
    field_states = serializers.SerializerMethodField()

    class Meta:
        model = UserBarcodeSettings
        fields = [
            "barcode",
            "associate_user_profile_with_barcode",
            "scanner_detection_enabled",
            "prefer_front_camera",
            "barcode_choices",
            "field_states",
        ]

    def _get_pull_settings_enabled(self):
        """Check if pull settings are enabled, using context when available."""
        pull_settings = self.context.get("pull_settings")
        if pull_settings is not None:
            return pull_settings.pull_setting == "Enable"
        user = self.context["request"].user
        try:
            ps = UserBarcodePullSettings.objects.get(user=user)
            return ps.pull_setting == "Enable"
        except UserBarcodePullSettings.DoesNotExist:
            return False

    @staticmethod
    def _has_profile(barcode):
        """Check if a barcode has a linked profile, using prefetch cache."""
        try:
            _ = barcode.barcodeuserprofile
            return True
        except Exception:
            return False

    @staticmethod
    def _barcode_to_choice(barcode, user):
        """Convert a barcode to a choice dict."""
        if barcode.barcode_type == "Identification":
            display = f"{user.username}'s identification barcode"
        elif barcode.barcode_type == "DynamicBarcode":
            owner_name = barcode.user.username if barcode.user != user else "Your"
            display = (
                f"{owner_name} Dynamic Barcode ending with " f"{barcode.barcode[-4:]}"
            )
        else:
            display = f"Your Barcode ending with {barcode.barcode[-4:]}"

        full_display = f"{barcode.barcode_type} - {barcode.barcode}"
        if barcode.user != user:
            full_display += f" (Owner: {barcode.user.username})"

        return {
            "id": barcode.id,
            "display": display,
            "barcode": barcode.barcode,
            "barcode_type": barcode.barcode_type,
            "full_display": full_display,
            "has_profile_addon": UserBarcodeSettingsSerializer._has_profile(barcode),
        }

    def get_barcode_choices(self, obj):
        """Get available barcode choices for the user.

        Uses prefetched barcodes from context when available (GET dashboard),
        falls back to DB queries otherwise (POST settings update).
        """
        user = self.context["request"].user

        # Use barcodes from context if available (already queried by view)
        barcodes = self.context.get("barcodes")
        if barcodes is not None:
            return [self._barcode_to_choice(b, user) for b in barcodes]

        # Fallback: query DB directly (for POST/PATCH paths)
        from django.db.models import Q

        qs = (
            Barcode.objects.filter(
                Q(barcode_type="DynamicBarcode")
                & (Q(user=user) | Q(share_with_others=True))
                | Q(
                    user=user,
                    barcode_type__in=["Identification", "Others"],
                )
            )
            .select_related("user")
            .prefetch_related("barcodeuserprofile")
            .order_by("-time_created")
        )
        return [self._barcode_to_choice(b, user) for b in qs]

    def get_field_states(self, obj):
        """Get field states based on current settings."""
        return {
            "associate_user_profile_disabled": False,
            "barcode_disabled": self._get_pull_settings_enabled(),
        }

    def validate(self, data):
        """Validation based on pull settings."""
        pull_settings_enabled = self._get_pull_settings_enabled()

        # If pull setting is enabled, barcode selection is not allowed
        barcode = data.get("barcode")
        if pull_settings_enabled and barcode is not None:
            raise serializers.ValidationError(
                {
                    "barcode": (
                        "Barcode selection is disabled when pull setting is " "enabled."
                    )
                }
            )

        # When selecting a dynamic barcode owned by someone else,
        # it must be shared_with_others
        user = self.context["request"].user
        if barcode is not None and not pull_settings_enabled:
            try:
                b = (
                    barcode
                    if isinstance(barcode, Barcode)
                    else Barcode.objects.get(pk=barcode)
                )
                if (
                    b.barcode_type == "DynamicBarcode"
                    and b.user != user
                    and not b.share_with_others
                ):
                    raise serializers.ValidationError(
                        {"barcode": ("Selected barcode is not shared by its owner.")}
                    )
            except Barcode.DoesNotExist:
                raise serializers.ValidationError(
                    {"barcode": "Selected barcode does not exist."}
                )

        return data
