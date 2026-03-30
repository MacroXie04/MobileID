from django.contrib.auth.models import User
from django.test import TestCase
from index.models import (
    Barcode,
    BarcodeUsage,
    BarcodeUserProfile,
)


class BarcodeSerializerTest(TestCase):
    """Test BarcodeSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

    def test_serializer_fields(self):
        """Test serializer includes all required fields"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        data = serializer.data

        expected_fields = [
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

        for field in expected_fields:
            self.assertIn(field, data)

    def test_usage_count_with_usage_record(self):
        """Test usage_count field with existing usage record"""
        from index.serializers import BarcodeSerializer

        BarcodeUsage.objects.create(barcode=self.barcode, total_usage=10)

        serializer = BarcodeSerializer(self.barcode)
        self.assertEqual(serializer.data["usage_count"], 10)

    def test_usage_count_without_usage_record(self):
        """Test usage_count field without usage record"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        self.assertEqual(serializer.data["usage_count"], 0)

    def test_display_name_identification(self):
        """Test display name for identification barcode"""
        from index.serializers import BarcodeSerializer

        self.barcode.barcode_type = "Identification"
        self.barcode.save()

        serializer = BarcodeSerializer(self.barcode)
        expected = "testuser's identification barcode"
        self.assertEqual(serializer.data["display_name"], expected)

    def test_display_name_dynamic(self):
        """Test display name for dynamic barcode"""
        from index.serializers import BarcodeSerializer

        self.barcode.barcode_type = "DynamicBarcode"
        self.barcode.save()

        serializer = BarcodeSerializer(self.barcode)
        expected = "Dynamic Barcode ending with 3456"
        self.assertEqual(serializer.data["display_name"], expected)

    def test_has_profile_addon_true(self):
        """Test has_profile_addon when profile exists"""
        from index.serializers import BarcodeSerializer

        BarcodeUserProfile.objects.create(
            linked_barcode=self.barcode,
            name="Test User",
            information_id="TEST123",
        )

        serializer = BarcodeSerializer(self.barcode)
        self.assertTrue(serializer.data["has_profile_addon"])

    def test_has_profile_addon_false(self):
        """Test has_profile_addon when profile doesn't exist"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        self.assertFalse(serializer.data["has_profile_addon"])
