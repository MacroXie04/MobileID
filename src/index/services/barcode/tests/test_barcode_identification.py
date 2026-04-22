"""Tests for index.services.barcode.identification.

Covers the three module-level callables:
- generate_unique_identification_barcode (collision retry + exhaustion)
- _carry_forward_identification_usage (aggregation across prior barcodes)
- _create_identification_barcode (rotation flow)
"""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from index.repositories import BarcodeRepository
from index.services.barcode.constants import BARCODE_IDENTIFICATION
from index.services.barcode.identification import (
    _carry_forward_identification_usage,
    _create_identification_barcode,
    generate_unique_identification_barcode,
)
from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin


class GenerateUniqueIdentificationBarcodeTest(DynamoDBCleanupMixin, TestCase):
    def test_returns_28_digit_string(self):
        code = generate_unique_identification_barcode()

        self.assertEqual(len(code), 28)
        self.assertTrue(code.isdigit())

    def test_retries_on_collision_then_returns_unique(self):
        # First two attempts collide, third succeeds.
        seen = {"count": 0}

        real_exists = BarcodeRepository.barcode_exists

        def _flaky(code):
            if seen["count"] < 2:
                seen["count"] += 1
                return True
            return real_exists(code)

        with patch.object(BarcodeRepository, "barcode_exists", side_effect=_flaky):
            code = generate_unique_identification_barcode(max_attempts=5)

        self.assertEqual(len(code), 28)
        self.assertEqual(seen["count"], 2)  # only the colliding attempts counted

    def test_raises_runtime_error_after_max_attempts(self):
        with patch.object(BarcodeRepository, "barcode_exists", return_value=True):
            with self.assertRaises(RuntimeError) as cm:
                generate_unique_identification_barcode(max_attempts=3)

        self.assertIn("after 3 attempts", str(cm.exception))


class CarryForwardIdentificationUsageTest(DynamoDBCleanupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="carryuser", password="pw")
        self.new_barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="9" * 28,
            barcode_type=BARCODE_IDENTIFICATION,
            owner_username=self.user.username,
        )

    def test_is_noop_when_no_old_barcodes(self):
        with patch.object(BarcodeRepository, "update") as mock_update:
            _carry_forward_identification_usage([], self.new_barcode)

        mock_update.assert_not_called()

    def test_sums_usage_and_takes_max_limits(self):
        old = [
            {
                "total_usage": 3,
                "total_usage_limit": 100,
                "daily_usage_limit": 10,
                "last_used": "2026-04-20T10:00:00Z",
            },
            {
                "total_usage": 5,
                "total_usage_limit": 50,
                "daily_usage_limit": 20,
                "last_used": "2026-04-21T10:00:00Z",
            },
        ]

        with patch.object(BarcodeRepository, "update") as mock_update:
            _carry_forward_identification_usage(old, self.new_barcode)

        mock_update.assert_called_once()
        kwargs = mock_update.call_args.kwargs
        self.assertEqual(kwargs["user_id"], self.new_barcode["user_id"])
        self.assertEqual(kwargs["barcode_uuid"], self.new_barcode["barcode_uuid"])
        self.assertEqual(kwargs["total_usage"], 8)
        self.assertEqual(kwargs["total_usage_limit"], 100)
        self.assertEqual(kwargs["daily_usage_limit"], 20)
        self.assertEqual(kwargs["last_used"], "2026-04-21T10:00:00Z")

    def test_omits_last_used_when_no_old_barcode_has_it(self):
        old = [
            {"total_usage": 1, "total_usage_limit": 10, "daily_usage_limit": 1},
        ]

        with patch.object(BarcodeRepository, "update") as mock_update:
            _carry_forward_identification_usage(old, self.new_barcode)

        kwargs = mock_update.call_args.kwargs
        self.assertNotIn("last_used", kwargs)

    def test_handles_missing_usage_fields_as_zero(self):
        old = [{}]  # completely empty prior record

        with patch.object(BarcodeRepository, "update") as mock_update:
            _carry_forward_identification_usage(old, self.new_barcode)

        kwargs = mock_update.call_args.kwargs
        self.assertEqual(kwargs["total_usage"], 0)
        self.assertEqual(kwargs["total_usage_limit"], 0)
        self.assertEqual(kwargs["daily_usage_limit"], 0)

    def test_coerces_string_numbers(self):
        # DynamoDB returns numeric attributes as Decimal/str — the function
        # casts via int(), so string digits must also work.
        old = [
            {
                "total_usage": "2",
                "total_usage_limit": "50",
                "daily_usage_limit": "5",
            },
        ]

        with patch.object(BarcodeRepository, "update") as mock_update:
            _carry_forward_identification_usage(old, self.new_barcode)

        kwargs = mock_update.call_args.kwargs
        self.assertEqual(kwargs["total_usage"], 2)
        self.assertEqual(kwargs["total_usage_limit"], 50)
        self.assertEqual(kwargs["daily_usage_limit"], 5)


class CreateIdentificationBarcodeTest(DynamoDBCleanupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="rotator", password="pw")

    def test_creates_new_barcode_when_user_has_none(self):
        new_bc = _create_identification_barcode(self.user)

        self.assertEqual(new_bc["barcode_type"], BARCODE_IDENTIFICATION)
        # Repository stores the raw value under the "barcode" attribute name.
        self.assertEqual(len(new_bc["barcode"]), 28)

        all_user = BarcodeRepository.get_user_barcodes_by_type(
            self.user.id, BARCODE_IDENTIFICATION
        )
        self.assertEqual(len(all_user), 1)
        self.assertEqual(all_user[0]["barcode_uuid"], new_bc["barcode_uuid"])

    def test_rotates_existing_barcode_and_preserves_usage(self):
        first = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1" * 28,
            barcode_type=BARCODE_IDENTIFICATION,
            owner_username=self.user.username,
        )
        BarcodeRepository.update(
            user_id=first["user_id"],
            barcode_uuid=first["barcode_uuid"],
            total_usage=7,
            total_usage_limit=99,
            daily_usage_limit=3,
        )

        new_bc = _create_identification_barcode(self.user)

        remaining = BarcodeRepository.get_user_barcodes_by_type(
            self.user.id, BARCODE_IDENTIFICATION
        )
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["barcode_uuid"], new_bc["barcode_uuid"])
        self.assertNotEqual(remaining[0]["barcode_uuid"], first["barcode_uuid"])
        self.assertEqual(int(remaining[0]["total_usage"]), 7)
        self.assertEqual(int(remaining[0]["total_usage_limit"]), 99)
        self.assertEqual(int(remaining[0]["daily_usage_limit"]), 3)

    def test_deletes_all_prior_identification_barcodes(self):
        for _ in range(3):
            BarcodeRepository.create(
                user_id=self.user.id,
                barcode_value=_fresh_value(),
                barcode_type=BARCODE_IDENTIFICATION,
                owner_username=self.user.username,
            )

        new_bc = _create_identification_barcode(self.user)

        remaining = BarcodeRepository.get_user_barcodes_by_type(
            self.user.id, BARCODE_IDENTIFICATION
        )
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["barcode_uuid"], new_bc["barcode_uuid"])


_counter = {"n": 0}


def _fresh_value() -> str:
    """Generate a unique 28-digit value for test fixtures."""
    _counter["n"] += 1
    return str(_counter["n"]).rjust(28, "0")
