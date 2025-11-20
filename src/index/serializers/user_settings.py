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
            # For School users: dynamic barcodes that are shared by others or owned by self  # noqa: E501
            all_dynamic_barcodes = (
                Barcode.objects.filter(barcode_type="DynamicBarcode")
                .select_related("user")
                .prefetch_related("barcodeuserprofile")
                .order_by("-time_created")
            )

            # Add dynamic barcodes (only show others' if they are shared)
            for b in all_dynamic_barcodes:
                if b.user != user and not b.share_with_others:
                    continue
                owner_name = b.user.username if b.user != user else "Your"
                display = (
                    f"{owner_name} Dynamic Barcode ending with "
                    f"{b.barcode[-4:]}"
                )

                # Check if barcode has profile
                has_profile = False
                try:
                    _ = b.barcodeuserprofile
                    has_profile = True
                except Exception:
                    pass

                choices.append(
                    {
                        "id": b.id,
                        "display": display,
                        "barcode": b.barcode,
                        "barcode_type": b.barcode_type,
                        "full_display": (
                            f"{b.barcode_type} - {b.barcode} "
                            f"(Owner: {b.user.username})"
                        ),
                        "has_profile_addon": has_profile,
                    }
                )

            # Get user's own identification and other barcodes
            own_other_barcodes = (
                Barcode.objects.filter(
                    user=user, barcode_type__in=["Identification", "Others"]
                )
                .prefetch_related("barcodeuserprofile")
                .order_by("-time_created")
            )

            for b in own_other_barcodes:
                if b.barcode_type == "Identification":
                    display = f"{user.username}'s identification barcode"
                else:  # Others type
                    display = f"Your Barcode ending with {b.barcode[-4:]}"

                # Check if barcode has profile
                has_profile = False
                try:
                    _ = b.barcodeuserprofile
                    has_profile = True
                except Exception:
                    pass

                choices.append(
                    {
                        "id": b.id,
                        "display": display,
                        "barcode": b.barcode,
                        "barcode_type": b.barcode_type,
                        "full_display": f"{b.barcode_type} - {b.barcode}",
                        "has_profile_addon": has_profile,
                    }
                )
        else:
            # Check if user is in User group - they only get identification
            # barcode
            is_user = user.groups.filter(name="User").exists()

            if is_user:
                # User type only sees identification barcode
                barcodes = (
                    Barcode.objects.filter(
                        user=user, barcode_type="Identification"
                    )
                    .prefetch_related("barcodeuserprofile")
                    .order_by("-time_created")
                )
            else:
                # Other non-School users see all their own barcodes
                barcodes = (
                    Barcode.objects.filter(user=user)
                    .prefetch_related("barcodeuserprofile")
                    .order_by("-time_created")
                )

            for b in barcodes:
                if b.barcode_type == "Identification":
                    display = f"{user.username}'s identification barcode"
                elif b.barcode_type == "DynamicBarcode":
                    display = f"Dynamic Barcode ending with {b.barcode[-4:]}"
                else:  # Others type
                    display = f"Barcode ending with {b.barcode[-4:]}"

                # Check if barcode has profile
                has_profile = False
                try:
                    _ = b.barcodeuserprofile
                    has_profile = True
                except Exception:
                    pass

                choices.append(
                    {
                        "id": b.id,
                        "display": display,
                        "barcode": b.barcode,
                        "barcode_type": b.barcode_type,
                        "full_display": f"{b.barcode_type} - {b.barcode}",
                        "has_profile_addon": has_profile,
                    }
                )

        return choices

    def get_field_states(self, obj):
        """Get field states based on user group and current settings"""
        user = self.context["request"].user
        is_user_group = user.groups.filter(name="User").exists()

        # Check if pull setting is enabled
        pull_settings_enabled = False
        try:
            pull_settings = UserBarcodePullSettings.objects.get(user=user)
            pull_settings_enabled = pull_settings.pull_setting == "Enable"
        except UserBarcodePullSettings.DoesNotExist:
            pass

        return {
            "associate_user_profile_disabled": is_user_group,
            # Disabled for User group only
            "barcode_disabled": pull_settings_enabled,
            # Disabled when pull setting is enabled
        }

    def validate(self, data):
        """Simple validation based on user group and pull settings"""
        user = self.context["request"].user
        is_user_group = user.groups.filter(name="User").exists()

        # Check if pull setting is enabled
        pull_settings_enabled = False
        try:
            pull_settings = UserBarcodePullSettings.objects.get(user=user)
            pull_settings_enabled = pull_settings.pull_setting == "Enable"
        except UserBarcodePullSettings.DoesNotExist:
            pass

        # Standard users cannot enable profile association
        if is_user_group and data.get(
            "associate_user_profile_with_barcode", False
        ):
            raise serializers.ValidationError(
                {
                    "associate_user_profile_with_barcode": (
                        "Standard users cannot enable profile association."
                    )
                }
            )

        # If pull setting is enabled, barcode selection is not allowed
        barcode = data.get("barcode")
        if pull_settings_enabled and barcode is not None:
            raise serializers.ValidationError(
                {
                    "barcode": (
                        "Barcode selection is disabled when pull setting is "
                        "enabled."
                    )
                }
            )

        # For School users, when selecting a dynamic barcode owned by someone
        # else,
        # it must be shared_with_others
        if barcode is not None and not pull_settings_enabled:
            try:
                # barcode can be an id or instance depending on partial update; ensure instance  # noqa: E501
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
                        {
                            "barcode": (
                                "Selected barcode is not shared by its owner."
                            )
                        }
                    )
            except Barcode.DoesNotExist:
                raise serializers.ValidationError(
                    {"barcode": "Selected barcode does not exist."}
                )

        return data
