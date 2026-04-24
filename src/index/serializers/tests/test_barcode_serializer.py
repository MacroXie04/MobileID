from django.contrib.auth.models import User
from django.test import TestCase

from index.repositories import BarcodeRepository, TransactionRepository
from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin as DynamoDBTestMixin


class BarcodeSerializerTest(DynamoDBTestMixin, TestCase):
    """Test BarcodeSerializer"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1234567890123456",
            barcode_type="Others",
            owner_username=self.user.username,
        )

    def test_serializer_fields(self):
        """Test serializer includes all required fields"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        data = serializer.data

        expected_fields = [
            "barcode_uuid",
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
        """Test usage_count field with existing usage data"""
        from index.serializers import BarcodeSerializer

        BarcodeRepository.update(
            user_id=self.barcode["user_id"],
            barcode_uuid=self.barcode["barcode_uuid"],
            total_usage=10,
        )
        # Re-fetch the barcode to get updated data
        barcode = BarcodeRepository.get_by_uuid(
            self.barcode["user_id"], self.barcode["barcode_uuid"]
        )

        serializer = BarcodeSerializer(barcode)
        self.assertEqual(serializer.data["usage_count"], 10)

    def test_usage_count_without_usage_record(self):
        """Test usage_count field with default (0) usage"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        self.assertEqual(serializer.data["usage_count"], 0)

    def test_display_name_dynamic(self):
        """Test display name for dynamic barcode"""
        from index.serializers import BarcodeSerializer

        dynamic_barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="9876543210123456",
            barcode_type="DynamicBarcode",
            owner_username=self.user.username,
        )

        serializer = BarcodeSerializer(dynamic_barcode)
        expected = "Dynamic Barcode ending with 3456"
        self.assertEqual(serializer.data["display_name"], expected)

    def test_has_profile_addon_true(self):
        """Test has_profile_addon when profile exists"""
        from index.serializers import BarcodeSerializer

        barcode_with_profile = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="withprofile12345",
            barcode_type="Others",
            owner_username=self.user.username,
            profile_name="Test User",
            profile_info_id="TEST123",
        )

        serializer = BarcodeSerializer(barcode_with_profile)
        self.assertTrue(serializer.data["has_profile_addon"])

    def test_has_profile_addon_false(self):
        """Test has_profile_addon when profile doesn't exist"""
        from index.serializers import BarcodeSerializer

        serializer = BarcodeSerializer(self.barcode)
        self.assertFalse(serializer.data["has_profile_addon"])

    def test_recent_transactions_caps_at_three(self):
        """recent_transactions must cap at 3 items, most-recent-first."""
        from datetime import timedelta

        from django.utils import timezone

        from index.serializers import BarcodeSerializer

        now = timezone.now()
        for i in range(5):
            TransactionRepository.create(
                user_id=self.user.id,
                barcode_uuid=self.barcode["barcode_uuid"],
                barcode_value=self.barcode.get("barcode"),
                time_created=(now - timedelta(minutes=i)).isoformat(),
            )

        serializer = BarcodeSerializer(self.barcode)
        recent = serializer.data["recent_transactions"]

        self.assertEqual(len(recent), 3)
        times = [r["time_created"] for r in recent]
        self.assertEqual(times, sorted(times, reverse=True))
        for entry in recent:
            self.assertIn("id", entry)
            self.assertIn("user", entry)
            self.assertIn("time_created", entry)
