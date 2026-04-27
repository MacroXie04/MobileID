from rest_framework import serializers

from index.repositories import BarcodeRepository, DuplicateBarcodeError


class BarcodeCreateSerializer(serializers.Serializer):
    """Serializer for creating new barcodes"""

    barcode = serializers.CharField()

    def validate_barcode(self, value):
        """Clean and validate barcode"""
        return value.strip()

    def create(self, validated_data):
        """Create barcode with automatic type detection"""
        user = self.context["request"].user
        barcode_value = validated_data["barcode"]

        # Check if 28-digit numeric -> DynamicBarcode
        is_28_digit = len(barcode_value) == 28 and barcode_value.isdigit()

        if is_28_digit:
            barcode_type = "DynamicBarcode"
            barcode_value = barcode_value[-14:]
        else:
            barcode_type = "Others"

        try:
            barcode_item = BarcodeRepository.create(
                user_id=user.id,
                barcode_value=barcode_value,
                barcode_type=barcode_type,
                owner_username=user.username,
            )
        except DuplicateBarcodeError:
            raise serializers.ValidationError(
                {"barcode": "This barcode already exists"}
            )

        return barcode_item


class DynamicBarcodeWithProfileSerializer(serializers.Serializer):
    """Serializer for creating dynamic barcode with profile information"""

    barcode = serializers.CharField(max_length=14, min_length=14)
    name = serializers.CharField(max_length=100)
    information_id = serializers.CharField(max_length=100)
    gender = serializers.ChoiceField(
        choices=[("Male", "Male"), ("Female", "Female"), ("Unknow", "Unknown")],
        default="Unknow",
    )
    avatar = serializers.CharField(required=False, allow_blank=True)

    def validate_barcode(self, value):
        """Validate barcode format - must be exactly 14 digits"""
        value = value.strip()
        if not value.isdigit():
            raise serializers.ValidationError("Barcode must contain only digits")
        if len(value) != 14:
            raise serializers.ValidationError(
                "Barcode must be exactly 14 digits for dynamic barcode"
            )
        return value

    def validate_name(self, value):
        return value.strip()

    def validate_information_id(self, value):
        return value.strip()

    def validate_avatar(self, value):
        """Validate and clean avatar Base64 string."""
        if not value:
            return None
        value = value.strip()

        if value.startswith("data:"):
            if "," in value:
                value = value.split(",", 1)[1]
            else:
                raise serializers.ValidationError(
                    "Invalid image format. Expected data URI with base64 content."
                )

        if value:
            import base64

            try:
                base64.b64decode(value, validate=True)
            except Exception:
                raise serializers.ValidationError(
                    "Invalid Base64 encoding. Please provide valid Base64 data."
                )

        return value if value else None

    def create(self, validated_data):
        """Create dynamic barcode with profile (denormalized into single item)."""
        user = self.context["request"].user
        barcode_value = validated_data["barcode"]

        # Check if barcode already exists
        if BarcodeRepository.barcode_exists(barcode_value):
            raise serializers.ValidationError(
                {"barcode": "This barcode already exists"}
            )

        try:
            barcode_item = BarcodeRepository.create(
                user_id=user.id,
                barcode_value=barcode_value,
                barcode_type="DynamicBarcode",
                owner_username=user.username,
                profile_name=validated_data["name"],
                profile_info_id=validated_data["information_id"],
                profile_gender=validated_data.get("gender", "Unknow"),
                profile_avatar=validated_data.get("avatar"),
            )
        except DuplicateBarcodeError:
            raise serializers.ValidationError(
                {"barcode": "This barcode already exists"}
            )

        return barcode_item
