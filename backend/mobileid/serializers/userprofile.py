from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from mobileid.models import Barcode, UserBarcodeSettings, UserProfile

from .barcode import BarcodeListSerializer


class StudentInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "name",
            "information_id",
            "user_profile_img",
            "is_locked",
            "failed_login_attempts",
            "locked_until"
        ]
        read_only_fields = ["is_locked", "failed_login_attempts", "locked_until"]


class UserProfileSerializer(serializers.ModelSerializer):
    userprofile = serializers.SerializerMethodField()
    account_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "userprofile", "is_active", "account_status"]
        read_only_fields = ["username", "is_active", "account_status"]

    def get_userprofile(self, obj):
        """Get user profile data, creating default if none exists"""
        try:
            user_profile = obj.userprofile
            return StudentInformationSerializer(user_profile).data
        except UserProfile.DoesNotExist:
            # Return default profile data if no profile exists
            return {
                "name": "Unknown User",
                "information_id": "N/A", 
                "user_profile_img": "",
                "is_locked": False,
                "failed_login_attempts": 0,
                "locked_until": None
            }

    def get_account_status(self, obj):
        """Get comprehensive account status for frontend"""
        try:
            user_profile = obj.userprofile
            now = timezone.now()

            # Check if account is locked
            is_locked = user_profile.is_locked
            locked_until = user_profile.locked_until

            # Check if lock has expired
            lock_expired = locked_until and locked_until < now

            # Determine overall status
            if not obj.is_active:
                return {
                    "status": "disabled",
                    "message": "Account is disabled",
                    "is_active": False,
                    "is_locked": False,
                    "lock_expired": False,
                    "failed_attempts": user_profile.failed_login_attempts
                }
            elif is_locked and not lock_expired:
                return {
                    "status": "locked",
                    "message": f"Account locked until {locked_until}",
                    "is_active": True,
                    "is_locked": True,
                    "lock_expired": False,
                    "failed_attempts": user_profile.failed_login_attempts,
                    "locked_until": locked_until
                }
            elif is_locked and lock_expired:
                return {
                    "status": "lock_expired",
                    "message": "Account lock has expired",
                    "is_active": True,
                    "is_locked": True,
                    "lock_expired": True,
                    "failed_attempts": user_profile.failed_login_attempts
                }
            else:
                return {
                    "status": "active",
                    "message": "Account is active",
                    "is_active": True,
                    "is_locked": False,
                    "lock_expired": False,
                    "failed_attempts": user_profile.failed_login_attempts
                }
        except UserProfile.DoesNotExist:
            return {
                "status": "no_profile",
                "message": "User profile not found",
                "is_active": obj.is_active,
                "is_locked": False,
                "lock_expired": False,
                "failed_attempts": 0
            }

    def update(self, instance, validated_data):
        info_data = validated_data.pop("userprofile", {})

        # Get or create user profile
        try:
            student_info = instance.userprofile
        except UserProfile.DoesNotExist:
            student_info = UserProfile.objects.create(
                user=instance,
                name="Unknown User",
                information_id="N/A",
                user_profile_img=""
            )

        # Update profile fields if provided
        for attr in ["name", "information_id", "user_profile_img"]:
            if attr in info_data:
                setattr(student_info, attr, info_data[attr])
        student_info.save()

        return super().update(instance, validated_data)


class UserBarcodeSettingsSerializer(serializers.ModelSerializer):
    available_barcodes = serializers.SerializerMethodField()

    barcode = serializers.PrimaryKeyRelatedField(
        queryset=Barcode.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = UserBarcodeSettings
        fields = [
            "barcode_pull",
            "barcode",
            "server_verification",
            "timestamp_verification",
            "available_barcodes",
        ]

    def get_available_barcodes(self, obj):
        user = obj.user
        barcodes = Barcode.objects.filter(user=user)
        return BarcodeListSerializer(barcodes, many=True).data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context.get("request").user
        if user:
            self.fields["barcode"].queryset = Barcode.objects.filter(user=user)

    def validate(self, data):
        user = self.context["request"].user
        has_barcodes = Barcode.objects.filter(user=user).exists()

        if not has_barcodes:
            data["barcode_pull"] = True

        pull_enabled = data.get(
            "barcode_pull", self.instance.barcode_pull if self.instance else True
        )
        selected_barcode = data.get("barcode")

        if not pull_enabled:
            if not selected_barcode:
                raise serializers.ValidationError(
                    {
                        "barcode": "Please select a barcode when Barcode Pull is disabled."
                    }
                )

        else:
            data["barcode"] = None

        return data
