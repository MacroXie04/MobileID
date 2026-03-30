from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from index.models import (
    Barcode,
    BarcodeUsage,
    Transaction,
)
from index.services.barcode.identification import _create_identification_barcode
from index.services.barcode.usage import _touch_barcode_usage
from index.services.barcode.utils import _random_digits
from index.services.barcode import generate_unique_identification_barcode


class BarcodeServiceTestBase(TestCase):
    """Base class with shared setUp for BarcodeServiceTest split."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.school_user = User.objects.create_user(
            username="schooluser", password="testpass123"
        )


class BarcodeServiceTest(BarcodeServiceTestBase):
    """Test barcode service functions — helpers, identification, and usage tracking"""

    def test_random_digits(self):
        """Test _random_digits helper function"""
        digits = _random_digits(10)
        self.assertEqual(len(digits), 10)
        self.assertTrue(digits.isdigit())

    def test_generate_unique_identification_barcode(self):
        """Test generating unique identification barcode"""
        barcode1 = generate_unique_identification_barcode()
        barcode2 = generate_unique_identification_barcode()

        self.assertEqual(len(barcode1), 28)
        self.assertEqual(len(barcode2), 28)
        self.assertTrue(barcode1.isdigit())
        self.assertTrue(barcode2.isdigit())
        self.assertNotEqual(barcode1, barcode2)

    @patch("index.services.barcode.identification.Barcode.objects.filter")
    def test_generate_unique_identification_barcode_max_attempts(self, mock_filter):
        """Test max attempts for unique barcode generation"""
        # Mock that all generated barcodes already exist
        mock_filter.return_value.exists.return_value = True

        with self.assertRaises(RuntimeError):
            generate_unique_identification_barcode(50)  # Pass max_attempts parameter

    def test_create_identification_barcode(self):
        """Test creating identification barcode"""
        # Create an existing identification barcode
        existing_barcode = Barcode.objects.create(
            user=self.user,
            barcode="1234567890123456789012345678",
            barcode_type="Identification",
        )

        # Create new identification barcode
        new_barcode = _create_identification_barcode(self.user)

        # Check that old barcode was deleted
        self.assertFalse(Barcode.objects.filter(id=existing_barcode.id).exists())

        # Check new barcode
        self.assertEqual(new_barcode.user, self.user)
        self.assertEqual(new_barcode.barcode_type, "Identification")
        self.assertEqual(len(new_barcode.barcode), 28)

    def test_touch_barcode_usage_new_barcode(self):
        """Test updating usage for barcode without existing usage record"""
        barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

        _touch_barcode_usage(barcode)

        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 1)

    def test_touch_barcode_usage_existing_barcode(self):
        """Test updating usage for barcode with existing usage record"""
        barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

        # Create initial usage
        BarcodeUsage.objects.create(barcode=barcode, total_usage=5)

        _touch_barcode_usage(barcode)

        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 6)

    def test_touch_barcode_usage_duplicate_within_5_minutes(self):
        """Test that duplicate usage within 5 minutes is not recorded"""
        barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

        # First usage - should record transaction and update usage
        _touch_barcode_usage(barcode, request_user=self.user)

        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 1)
        self.assertEqual(
            Transaction.objects.filter(user=self.user, barcode_used=barcode).count(), 1
        )

        # Second usage within 5 minutes - should NOT record anything
        _touch_barcode_usage(barcode, request_user=self.user)

        usage.refresh_from_db()
        self.assertEqual(usage.total_usage, 1)  # Still 1, not incremented
        self.assertEqual(
            Transaction.objects.filter(user=self.user, barcode_used=barcode).count(), 1
        )

    def test_touch_barcode_usage_after_5_minutes(self):
        """Test that usage after 5 minutes is recorded"""
        from datetime import timedelta

        from django.utils import timezone

        barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

        # First usage
        _touch_barcode_usage(barcode, request_user=self.user)

        # Simulate transaction created 6 minutes ago
        old_time = timezone.now() - timedelta(minutes=6)
        Transaction.objects.filter(user=self.user, barcode_used=barcode).update(
            time_created=old_time
        )

        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 1)

        # Second usage after 5 minutes - should record new transaction
        _touch_barcode_usage(barcode, request_user=self.user)

        usage.refresh_from_db()
        self.assertEqual(usage.total_usage, 2)  # Now 2
        self.assertEqual(
            Transaction.objects.filter(user=self.user, barcode_used=barcode).count(), 2
        )

    def test_touch_barcode_usage_different_users_within_5_minutes(self):
        """Test that different users can use the same barcode within 5 minutes"""
        barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

        # First user uses barcode
        _touch_barcode_usage(barcode, request_user=self.user)

        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 1)
        self.assertEqual(Transaction.objects.filter(barcode_used=barcode).count(), 1)

        # Different user uses same barcode within 5 minutes - should record
        _touch_barcode_usage(barcode, request_user=self.school_user)

        usage.refresh_from_db()
        self.assertEqual(usage.total_usage, 2)  # Should be 2
        self.assertEqual(Transaction.objects.filter(barcode_used=barcode).count(), 2)

    def test_touch_barcode_usage_no_request_user(self):
        """Test usage without request_user updates BarcodeUsage but no Transaction"""
        barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

        # Usage without request_user - updates BarcodeUsage, no Transaction
        _touch_barcode_usage(barcode, request_user=None)

        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 1)
        self.assertEqual(Transaction.objects.filter(barcode_used=barcode).count(), 0)

        # Second call without request_user - still updates (no 5-min check)
        _touch_barcode_usage(barcode, request_user=None)

        usage.refresh_from_db()
        self.assertEqual(usage.total_usage, 2)
