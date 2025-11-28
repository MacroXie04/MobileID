from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.utils import timezone
from index.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
    Transaction,
)
from index.services.barcode import (
    generate_barcode,
    generate_unique_identification_barcode,
    _create_identification_barcode,
    _touch_barcode_usage,
    _random_digits,
)
from index.services.usage_limit import UsageLimitService


class BarcodeServiceTest(TestCase):
    """Test barcode service functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.school_user = User.objects.create_user(
            username="schooluser", password="testpass123"
        )
        self.staff_user = User.objects.create_user(
            username="staffuser", password="testpass123"
        )

        # Create groups
        self.user_group = Group.objects.create(name="User")
        self.school_group = Group.objects.create(name="School")
        self.staff_group = Group.objects.create(name="Staff")

        # Assign users to groups
        self.user.groups.add(self.user_group)
        self.school_user.groups.add(self.school_group)
        self.staff_user.groups.add(self.staff_group)

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

    @patch("index.services.barcode.Barcode.objects.filter")
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
        self.assertEqual(Transaction.objects.filter(user=self.user, barcode_used=barcode).count(), 1)

        # Second usage within 5 minutes - should NOT record anything
        _touch_barcode_usage(barcode, request_user=self.user)

        usage.refresh_from_db()
        self.assertEqual(usage.total_usage, 1)  # Still 1, not incremented
        self.assertEqual(Transaction.objects.filter(user=self.user, barcode_used=barcode).count(), 1)

    def test_touch_barcode_usage_after_5_minutes(self):
        """Test that usage after 5 minutes is recorded"""
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
        self.assertEqual(Transaction.objects.filter(user=self.user, barcode_used=barcode).count(), 2)

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
        """Test that usage without request_user still updates BarcodeUsage but no Transaction"""
        barcode = Barcode.objects.create(
            user=self.user, barcode="1234567890123456", barcode_type="Others"
        )

        # Usage without request_user - should update BarcodeUsage but not create Transaction
        _touch_barcode_usage(barcode, request_user=None)

        usage = BarcodeUsage.objects.get(barcode=barcode)
        self.assertEqual(usage.total_usage, 1)
        self.assertEqual(Transaction.objects.filter(barcode_used=barcode).count(), 0)

        # Second call without request_user - should still update (no 5-min check applies)
        _touch_barcode_usage(barcode, request_user=None)

        usage.refresh_from_db()
        self.assertEqual(usage.total_usage, 2)

    def test_generate_barcode_staff_user(self):
        """Test barcode generation for staff user (should fail)"""
        result = generate_barcode(self.staff_user)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Staff accounts cannot generate barcodes.")

    def test_generate_barcode_invalid_group(self):
        """Test barcode generation for user with no valid group"""
        user_no_group = User.objects.create_user(username="nogroup", password="test123")

        result = generate_barcode(user_no_group)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Permission Denied.")

    def test_generate_barcode_user_group_new(self):
        """Test barcode generation for User group member without existing barcode"""  # noqa: E501
        result = generate_barcode(self.user)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "Identification")
        self.assertEqual(len(result["barcode"]), 28)

        # Check that identification barcode was created
        barcode = Barcode.objects.get(user=self.user, barcode_type="Identification")
        self.assertEqual(barcode.barcode, result["barcode"])

    def test_generate_barcode_user_group_existing(self):
        """Test barcode generation for User group member with existing barcode"""  # noqa: E501
        # Create existing identification barcode
        existing_barcode = Barcode.objects.create(
            user=self.user,
            barcode="1234567890123456789012345678",
            barcode_type="Identification",
        )

        result = generate_barcode(self.user)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "Identification")

        # Check that new barcode was created and old one was deleted
        self.assertFalse(Barcode.objects.filter(id=existing_barcode.id).exists())
        new_barcode = Barcode.objects.get(user=self.user, barcode_type="Identification")
        self.assertNotEqual(new_barcode.barcode, existing_barcode.barcode)

    def test_generate_barcode_school_group_no_selection(self):
        """Test barcode generation for School group member with no barcode selected"""  # noqa: E501
        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No barcode selected.")

    def test_generate_barcode_school_group_dynamic(self):
        """Test barcode generation for School group member with dynamic barcode"""  # noqa: E501
        dynamic_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        UserBarcodeSettings.objects.create(
            user=self.school_user, barcode=dynamic_barcode
        )

        with patch("index.services.barcode._timestamp", return_value="20231201120000"):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "DynamicBarcode")
        self.assertEqual(result["barcode"], "2023120112000012345678901234")
        self.assertIn("Dynamic: 1234", result["message"])

    def test_generate_barcode_school_group_others(self):
        """Test barcode generation for School group member with Others barcode"""  # noqa: E501
        other_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="static123456789",
            barcode_type="Others",
        )

        UserBarcodeSettings.objects.create(user=self.school_user, barcode=other_barcode)

        result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["barcode_type"], "Others")
        self.assertEqual(result["barcode"], "static123456789")
        self.assertIn("Barcode ending with 6789", result["message"])

    def test_generate_barcode_dynamic_with_server_verification_disabled(self):
        """Test dynamic barcode generation with server verification disabled"""
        dynamic_barcode = Barcode.objects.create(
            user=self.school_user,
            barcode="12345678901234",
            barcode_type="DynamicBarcode",
        )

        UserBarcodeSettings.objects.create(
            user=self.school_user,
            barcode=dynamic_barcode,
            server_verification=False,  # Disabled to avoid session attribute error  # noqa: E501
        )

        with patch("index.services.barcode._timestamp", return_value="20231201120000"):
            result = generate_barcode(self.school_user)

        self.assertEqual(result["status"], "success")
        self.assertIn("Dynamic: 1234", result["message"])


class UsageLimitServiceTest(TestCase):
    """Unit tests for UsageLimitService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="limituser", password="testpass123"
        )
        self.barcode = Barcode.objects.create(
            user=self.user, barcode="limit-123456", barcode_type="Others"
        )

    def test_check_daily_limit_no_record_or_zero_limit(self):
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertTrue(allowed)
        self.assertIsNone(msg)
        # Create usage with zero limit
        BarcodeUsage.objects.create(barcode=self.barcode, daily_usage_limit=0)
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertTrue(allowed)
        self.assertIsNone(msg)

    def test_check_daily_limit_enforced(self):
        _ = BarcodeUsage.objects.create(
            barcode=self.barcode, daily_usage_limit=2, total_usage=0
        )
        # No transactions yet
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertTrue(allowed)
        # Create two transactions for today
        Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        allowed, msg = UsageLimitService.check_daily_limit(self.barcode)
        self.assertFalse(allowed)
        self.assertIn("Daily usage limit of 2", msg)

    def test_check_total_limit(self):
        # No record allows
        allowed, msg = UsageLimitService.check_total_limit(self.barcode)
        self.assertTrue(allowed)
        # With limit not reached
        usage = BarcodeUsage.objects.create(
            barcode=self.barcode, total_usage_limit=3, total_usage=2
        )
        allowed, msg = UsageLimitService.check_total_limit(self.barcode)
        self.assertTrue(allowed)
        # Reached
        usage.total_usage = 3
        usage.save()
        allowed, msg = UsageLimitService.check_total_limit(self.barcode)
        self.assertFalse(allowed)
        self.assertIn("Total usage limit of 3", msg)

    def test_get_usage_stats_defaults_and_values(self):
        stats = UsageLimitService.get_usage_stats(self.barcode)
        self.assertEqual(stats["daily_used"], 0)
        self.assertEqual(stats["daily_limit"], 0)
        self.assertIsNone(stats["daily_remaining"])
        # Create usage and transactions
        BarcodeUsage.objects.create(
            barcode=self.barcode,
            daily_usage_limit=5,
            total_usage_limit=10,
            total_usage=7,
        )
        Transaction.objects.create(user=self.user, barcode_used=self.barcode)
        stats = UsageLimitService.get_usage_stats(self.barcode)
        self.assertEqual(stats["daily_used"], 1)
        self.assertEqual(stats["daily_remaining"], 4)
        self.assertEqual(stats["total_used"], 7)
        self.assertEqual(stats["total_remaining"], 3)
