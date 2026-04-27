from rest_framework import serializers

from index.repositories import BarcodeRepository


class UserBarcodePullSettingsSerializer(serializers.Serializer):
    """Serializer for user barcode pull settings"""

    pull_setting = serializers.ChoiceField(
        choices=[("Enable", "Enable"), ("Disable", "Disable")],
        default="Disable",
    )
    gender_setting = serializers.ChoiceField(
        choices=[("Male", "Male"), ("Female", "Female"), ("Unknow", "Unknow")],
        default="Unknow",
    )


class UserBarcodeSettingsSerializer(serializers.Serializer):
    """Serializer for user barcode settings (DynamoDB-backed)."""

    barcode = serializers.CharField(
        required=False, allow_null=True, source="active_barcode_uuid"
    )
    associate_user_profile_with_barcode = serializers.BooleanField(default=False)
    scanner_detection_enabled = serializers.BooleanField(default=False)
    prefer_front_camera = serializers.BooleanField(default=True)
    barcode_choices = serializers.SerializerMethodField()
    field_states = serializers.SerializerMethodField()

    def _get_pull_settings_enabled(self):
        """Check if pull settings are enabled, using context when available."""
        pull_settings = self.context.get("pull_settings")
        if pull_settings is not None:
            if isinstance(pull_settings, dict):
                return pull_settings.get("pull_setting") == "Enable"
            return pull_settings.pull_setting == "Enable"
        return False

    @staticmethod
    def _barcode_to_choice(barcode_item, user):
        """Convert a DynamoDB barcode dict to a choice dict."""
        barcode_type = barcode_item.get("barcode_type")
        barcode_val = barcode_item.get("barcode", "")
        owner = barcode_item.get("owner_username", "Unknown")
        is_own = barcode_item.get("user_id") == str(user.id)

        if barcode_type == "DynamicBarcode":
            owner_label = "Your" if is_own else owner
            display = f"{owner_label} Dynamic Barcode ending with {barcode_val[-4:]}"
        else:
            display = f"Your Barcode ending with {barcode_val[-4:]}"

        full_display = f"{barcode_type} - {barcode_val}"
        if not is_own:
            full_display += f" (Owner: {owner})"

        return {
            "id": barcode_item.get("barcode_uuid"),
            "display": display,
            "barcode": barcode_val,
            "barcode_type": barcode_type,
            "full_display": full_display,
            "has_profile_addon": bool(barcode_item.get("profile_name")),
        }

    def get_barcode_choices(self, obj):
        """Get available barcode choices for the user."""
        user = self.context["request"].user

        # Use barcodes from context if available (already queried by view)
        barcodes = self.context.get("barcodes")
        if barcodes is not None:
            return [self._barcode_to_choice(b, user) for b in barcodes]

        # Fallback: query DynamoDB directly
        barcodes = BarcodeRepository.get_dashboard_barcodes(user.id)
        return [self._barcode_to_choice(b, user) for b in barcodes]

    def get_field_states(self, obj):
        return {
            "associate_user_profile_disabled": False,
            "barcode_disabled": self._get_pull_settings_enabled(),
        }

    def validate(self, data):
        """Validation based on pull settings."""
        pull_settings_enabled = self._get_pull_settings_enabled()

        barcode_uuid = data.get("active_barcode_uuid")
        if pull_settings_enabled and barcode_uuid is not None:
            raise serializers.ValidationError(
                {
                    "barcode": (
                        "Barcode selection is disabled when pull setting is enabled."
                    )
                }
            )

        user = self.context["request"].user
        if barcode_uuid is not None and not pull_settings_enabled:
            barcode_item = BarcodeRepository.get_by_uuid(user.id, barcode_uuid)
            if not barcode_item:
                # Dashboard choices are bounded. If a shared barcode is not in
                # that choice set, it is not selectable from this request.
                dashboard_barcodes = self.context.get("barcodes")
                if dashboard_barcodes is None:
                    dashboard_barcodes = BarcodeRepository.get_dashboard_barcodes(
                        user.id
                    )
                barcode_item = next(
                    (
                        b
                        for b in dashboard_barcodes
                        if b.get("barcode_uuid") == barcode_uuid
                    ),
                    None,
                )

            if not barcode_item:
                raise serializers.ValidationError(
                    {"barcode": "Selected barcode does not exist."}
                )

            if (
                barcode_item.get("barcode_type") == "DynamicBarcode"
                and barcode_item.get("user_id") != str(user.id)
                and not barcode_item.get("share_with_others", False)
            ):
                raise serializers.ValidationError(
                    {"barcode": "Selected barcode is not shared by its owner."}
                )

            data["active_barcode_owner_id"] = barcode_item.get("user_id", str(user.id))

        return data
