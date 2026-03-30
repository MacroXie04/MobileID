from index.models import Barcode, BarcodeUserProfile
from rest_framework import serializers


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

        # Check if 28-digit numeric → DynamicBarcode
        is_28_digit = len(barcode_value) == 28 and barcode_value.isdigit()

        if is_28_digit:
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
        """Clean name field"""
        return value.strip()

    def validate_information_id(self, value):
        """Clean information ID field"""
        return value.strip()

    def validate_avatar(self, value):
        """Validate and clean avatar Base64 string.

        Accepts formats like:
        - data:image/jpeg;base64,xxxxx
        - data:image/png;base64,xxxxx
        - Pure base64 string without prefix
        """
        if not value:
            return None
        value = value.strip()

        # Remove data URI prefix if present (e.g., data:image/jpeg;base64,)
        if value.startswith("data:"):
            # Extract base64 part after comma
            if "," in value:
                value = value.split(",", 1)[1]
            else:
                # Invalid data URI format
                raise serializers.ValidationError(
                    "Invalid image format. Expected data URI with base64 content."
                )

        # Basic validation: check if it looks like base64
        if value:
            import base64

            try:
                # Try to decode to verify it's valid base64
                base64.b64decode(value, validate=True)
            except Exception:
                raise serializers.ValidationError(
                    "Invalid Base64 encoding. Please provide valid Base64 data."
                )

        return value if value else None

    def create(self, validated_data):
        """Create dynamic barcode with profile"""
        user = self.context["request"].user
        barcode_value = validated_data["barcode"]

        # Check if barcode already exists
        if Barcode.objects.filter(barcode=barcode_value).exists():
            raise serializers.ValidationError(
                {"barcode": "This barcode already exists"}
            )

        # Create barcode
        barcode_obj = Barcode.objects.create(
            user=user,
            barcode=barcode_value,
            barcode_type="DynamicBarcode",
        )

        # Create profile with optional avatar
        BarcodeUserProfile.objects.create(
            linked_barcode=barcode_obj,
            name=validated_data["name"],
            information_id=validated_data["information_id"],
            gender_barcode=validated_data.get("gender", "Unknow"),
            user_profile_img=validated_data.get("avatar"),
        )

        return barcode_obj
