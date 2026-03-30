from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase
from index.models import (
    Barcode,
    UserBarcodeSettings,
)


class BarcodeCreateSerializerTest(TestCase):
    """Test BarcodeCreateSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_validate_barcode_strips_whitespace(self):
        """Test that barcode validation strips whitespace"""
        from index.serializers import BarcodeCreateSerializer

        serializer = BarcodeCreateSerializer()
        result = serializer.validate_barcode("  test123  ")
        self.assertEqual(result, "test123")

    def test_create_dynamic_barcode(self):
        """Test creating dynamic barcode from 28-digit input"""
        from index.serializers import BarcodeCreateSerializer

        data = {"barcode": "1234567890123456789012345678"}  # 28 digits
        context = {"request": Mock(user=self.user)}

        serializer = BarcodeCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())

        barcode = serializer.save()
        self.assertEqual(barcode.barcode_type, "DynamicBarcode")
        self.assertEqual(barcode.barcode, "56789012345678")  # Last 14 digits

    def test_create_others_barcode(self):
        """Test creating Others type barcode"""
        from index.serializers import BarcodeCreateSerializer

        data = {"barcode": "regular-barcode-123"}
        context = {"request": Mock(user=self.user)}

        serializer = BarcodeCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())

        barcode = serializer.save()
        self.assertEqual(barcode.barcode_type, "Others")
        self.assertEqual(barcode.barcode, "regular-barcode-123")


class UserBarcodeSettingsSerializerTest(TestCase):
    """Test UserBarcodeSettingsSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_field_states_profile_association_not_disabled(self):
        """Test field states: associate_user_profile_disabled is always False"""
        from index.serializers import UserBarcodeSettingsSerializer

        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {"request": Mock(user=self.user)}

        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        field_states = serializer.data["field_states"]

        self.assertFalse(field_states["associate_user_profile_disabled"])
        self.assertFalse(field_states["barcode_disabled"])

    def test_barcode_choices_includes_all_types(self):
        """Test barcode choices include all barcode types"""
        from index.serializers import UserBarcodeSettingsSerializer

        # Create barcodes of different types
        dynamic_barcode = Barcode.objects.create(
            user=self.user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )
        ident_barcode = Barcode.objects.create(
            user=self.user,
            barcode="1234567890123456789012345678",
            barcode_type="Identification",
        )
        other_barcode = Barcode.objects.create(
            user=self.user,
            barcode="other123456789",
            barcode_type="Others",
        )

        settings = UserBarcodeSettings.objects.create(user=self.user)
        context = {"request": Mock(user=self.user)}

        serializer = UserBarcodeSettingsSerializer(settings, context=context)
        choices = serializer.data["barcode_choices"]

        # Should have all 3 barcodes
        self.assertEqual(len(choices), 3)
        choice_ids = {c["id"] for c in choices}
        self.assertIn(dynamic_barcode.id, choice_ids)
        self.assertIn(ident_barcode.id, choice_ids)
        self.assertIn(other_barcode.id, choice_ids)
