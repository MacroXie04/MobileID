from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from index.repositories import BarcodeRepository, TransactionRepository
from index.services.barcode.usage import _touch_barcode_usage
from index.services.barcode.utils import _random_digits
from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin as DynamoDBTestMixin


class BarcodeServiceTestBase(DynamoDBTestMixin, TestCase):
    """Base class with shared setUp for BarcodeServiceTest split."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.school_user = User.objects.create_user(
            username="schooluser", password="testpass123"
        )


class BarcodeServiceTest(BarcodeServiceTestBase):
    """Test barcode service functions -- helpers and usage tracking"""

    def test_random_digits(self):
        """Test _random_digits helper function"""
        digits = _random_digits(10)
        self.assertEqual(len(digits), 10)
        self.assertTrue(digits.isdigit())

    def test_touch_barcode_usage_new_barcode(self):
        """Test updating usage for barcode without existing usage record"""
        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1234567890123456",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        _touch_barcode_usage(barcode)

        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 1)

    def test_touch_barcode_usage_existing_barcode(self):
        """Test updating usage for barcode with existing usage record"""
        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1234567890123456",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        # Set initial usage to 5
        BarcodeRepository.update(
            user_id=barcode["user_id"],
            barcode_uuid=barcode["barcode_uuid"],
            total_usage=5,
        )
        barcode["total_usage"] = 5

        _touch_barcode_usage(barcode)

        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 6)

    def test_touch_barcode_usage_duplicate_within_5_minutes(self):
        """Test that duplicate usage within 5 minutes is not recorded"""
        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1234567890123456",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        # First usage - should record transaction and update usage
        _touch_barcode_usage(barcode, request_user=self.user)

        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 1)

        txns = TransactionRepository.for_barcode(barcode["barcode_uuid"])
        self.assertEqual(len(txns), 1)

        # Second usage within 5 minutes - should NOT record anything
        _touch_barcode_usage(barcode, request_user=self.user)

        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 1)  # Still 1, not incremented

        txns = TransactionRepository.for_barcode(barcode["barcode_uuid"])
        self.assertEqual(len(txns), 1)

    def test_touch_barcode_usage_after_5_minutes(self):
        """Test that usage after 5 minutes is recorded"""
        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1234567890123456",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        # First usage
        _touch_barcode_usage(barcode, request_user=self.user)

        # Manually create a backdated transaction (simulating 6 minutes ago)
        # First, check current state
        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 1)

        # Delete the recent transaction and create an old one
        old_time = (timezone.now() - timedelta(minutes=6)).isoformat()
        # We can't easily backdate existing DynamoDB items, so we create a new
        # transaction with an old timestamp. The recent_user_barcode_usage check
        # filters by time_created >= cutoff, so if the only transaction is old,
        # the second call should succeed.

        # For this test we need to work around the fact that we already have a
        # recent transaction. Instead, let's test with a fresh barcode and
        # pre-create an old transaction.
        barcode2 = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="9999888877776666",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        # Create old transaction (6 minutes ago)
        old_time = (timezone.now() - timedelta(minutes=6)).isoformat()
        TransactionRepository.create(
            user_id=self.user.id,
            barcode_uuid=barcode2["barcode_uuid"],
            barcode_value=barcode2["barcode"],
            time_created=old_time,
        )
        # Also increment usage to simulate that first usage happened
        BarcodeRepository.increment_usage(
            user_id=barcode2["user_id"],
            barcode_uuid=barcode2["barcode_uuid"],
        )

        updated2 = BarcodeRepository.get_by_uuid(
            barcode2["user_id"], barcode2["barcode_uuid"]
        )
        self.assertEqual(int(updated2["total_usage"]), 1)

        # Second usage after 5 minutes - should record new transaction
        _touch_barcode_usage(barcode2, request_user=self.user)

        updated2 = BarcodeRepository.get_by_uuid(
            barcode2["user_id"], barcode2["barcode_uuid"]
        )
        self.assertEqual(int(updated2["total_usage"]), 2)  # Now 2

        txns = TransactionRepository.for_barcode(barcode2["barcode_uuid"])
        self.assertEqual(len(txns), 2)

    def test_touch_barcode_usage_different_users_within_5_minutes(self):
        """Test that different users can use the same barcode within 5 minutes"""
        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1234567890123456",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        # First user uses barcode
        _touch_barcode_usage(barcode, request_user=self.user)

        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 1)

        txns = TransactionRepository.for_barcode(barcode["barcode_uuid"])
        self.assertEqual(len(txns), 1)

        # Different user uses same barcode within 5 minutes - should record
        _touch_barcode_usage(barcode, request_user=self.school_user)

        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 2)  # Should be 2

        txns = TransactionRepository.for_barcode(barcode["barcode_uuid"])
        self.assertEqual(len(txns), 2)

    def test_touch_barcode_usage_no_request_user(self):
        """Test usage without request_user updates usage but no Transaction"""
        barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1234567890123456",
            barcode_type="Others",
            owner_username=self.user.username,
        )

        # Usage without request_user - updates usage, no Transaction
        _touch_barcode_usage(barcode, request_user=None)

        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 1)

        txns = TransactionRepository.for_barcode(barcode["barcode_uuid"])
        self.assertEqual(len(txns), 0)

        # Second call without request_user - still updates (no 5-min check)
        _touch_barcode_usage(barcode, request_user=None)

        updated = BarcodeRepository.get_by_uuid(
            barcode["user_id"], barcode["barcode_uuid"]
        )
        self.assertEqual(int(updated["total_usage"]), 2)
