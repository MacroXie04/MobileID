from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.utils import timezone

from index.repositories import BarcodeRepository, TransactionRepository
from index.services.transactions import TransactionService
from index.services.transaction_writes import TransactionWriteMixin, CreatedTransaction
from index.services.transaction_queries import TransactionQueryMixin
from index.tests.dynamodb_cleanup import DynamoDBCleanupMixin as DynamoDBTestMixin


class TransactionWriteServiceTests(DynamoDBTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="txwriter", password="pass123")
        self.barcode = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1234567890123456",
            barcode_type="DynamicBarcode",
            owner_username=self.user.username,
        )

    def test_create_transaction_success(self):
        tx = TransactionWriteMixin.create_transaction(
            user=self.user, barcode=self.barcode
        )
        self.assertIsNotNone(tx)
        self.assertIn("sk", tx)
        self.assertEqual(tx["user_id"], str(self.user.id))
        self.assertEqual(tx["barcode_uuid"], self.barcode["barcode_uuid"])

    def test_create_transaction_requires_barcode(self):
        with self.assertRaises(ValueError) as ctx:
            TransactionWriteMixin.create_transaction(user=self.user, barcode=None)
        self.assertIn("barcode", str(ctx.exception).lower())

    def test_create_transaction_accepts_dict_barcode(self):
        """Dict barcodes (from DynamoDB) are the primary input type."""
        tx = TransactionWriteMixin.create_transaction(
            user=self.user, barcode=self.barcode
        )
        self.assertIsNotNone(tx)
        self.assertEqual(tx["barcode_uuid"], self.barcode["barcode_uuid"])

    def test_create_transaction_rejects_invalid_user(self):
        with self.assertRaises(ValueError):
            TransactionWriteMixin.create_transaction(
                user="not-a-user", barcode=self.barcode
            )

    def test_create_transaction_rejects_anonymous_user(self):
        with self.assertRaises((PermissionError, ValueError)):
            TransactionWriteMixin.create_transaction(
                user=AnonymousUser(), barcode=self.barcode
            )

    def test_bulk_ingest_success(self):
        user2 = User.objects.create_user(username="txwriter2", password="pass123")
        barcode2 = BarcodeRepository.create(
            user_id=user2.id,
            barcode_value="9876543210123456",
            barcode_type="Others",
            owner_username=user2.username,
        )
        rows = [
            {"user": self.user, "barcode": self.barcode},
            {"user": user2, "barcode": barcode2},
        ]
        results = TransactionWriteMixin.bulk_ingest(rows)
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], CreatedTransaction)
        self.assertEqual(results[0].user_id, self.user.id)
        self.assertEqual(results[1].user_id, user2.id)

    def test_bulk_ingest_rejects_missing_barcode(self):
        rows = [{"user": self.user, "barcode": None}]
        with self.assertRaises(ValueError) as ctx:
            TransactionWriteMixin.bulk_ingest(rows)
        self.assertIn("Row 0", str(ctx.exception))


class TransactionQueryServiceTests(DynamoDBTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="txreader", password="pass123")
        self.user2 = User.objects.create_user(username="txreader2", password="pass123")
        self.barcode1 = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="1111111111111111",
            barcode_type="DynamicBarcode",
            owner_username=self.user.username,
        )
        self.barcode2 = BarcodeRepository.create(
            user_id=self.user.id,
            barcode_value="2222222222222222",
            barcode_type="Others",
            owner_username=self.user.username,
        )

    def _create_tx(self, user, barcode, time_created=None):
        """Create a transaction, optionally with a specific timestamp."""
        when = time_created.isoformat() if time_created else None
        return TransactionRepository.create(
            user_id=user.id,
            barcode_uuid=barcode["barcode_uuid"],
            barcode_value=barcode.get("barcode"),
            time_created=when,
        )

    def test_for_user_returns_ordered_transactions(self):
        now = timezone.now()
        tx1 = self._create_tx(self.user, self.barcode1, now - timedelta(hours=2))
        tx2 = self._create_tx(self.user, self.barcode1, now - timedelta(hours=1))
        # Other user's transaction should not appear
        self._create_tx(self.user2, self.barcode2, now)

        results = TransactionQueryMixin.for_user(self.user)
        self.assertEqual(len(results), 2)
        # Most recent first
        self.assertEqual(results[0]["sk"], tx2["sk"])
        self.assertEqual(results[1]["sk"], tx1["sk"])

    def test_for_user_with_since_filter(self):
        now = timezone.now()
        self._create_tx(self.user, self.barcode1, now - timedelta(days=2))
        tx_recent = self._create_tx(self.user, self.barcode1, now - timedelta(hours=1))

        results = TransactionQueryMixin.for_user(
            self.user, since=now - timedelta(days=1)
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sk"], tx_recent["sk"])

    def test_for_user_with_until_filter(self):
        now = timezone.now()
        tx_old = self._create_tx(self.user, self.barcode1, now - timedelta(days=2))
        self._create_tx(self.user, self.barcode1, now - timedelta(hours=1))

        results = TransactionQueryMixin.for_user(
            self.user, until=now - timedelta(days=1)
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sk"], tx_old["sk"])

    def test_top_barcodes_returns_ranked_list(self):
        now = timezone.now()
        # barcode1 used 3 times, barcode2 used 1 time
        for i in range(3):
            self._create_tx(self.user, self.barcode1, now - timedelta(minutes=i))
        self._create_tx(self.user, self.barcode2, now)

        results = TransactionQueryMixin.top_barcodes()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], self.barcode1["barcode_uuid"])
        self.assertEqual(results[0][1], 3)
        self.assertEqual(results[1][0], self.barcode2["barcode_uuid"])
        self.assertEqual(results[1][1], 1)

    def test_top_barcodes_with_limit(self):
        now = timezone.now()
        for i in range(3):
            self._create_tx(self.user, self.barcode1, now - timedelta(minutes=i))
        self._create_tx(self.user, self.barcode2, now)

        results = TransactionQueryMixin.top_barcodes(limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], self.barcode1["barcode_uuid"])

    def test_usage_over_time_day_granularity(self):
        now = timezone.now()
        # Two transactions today
        self._create_tx(self.user, self.barcode1, now - timedelta(hours=1))
        self._create_tx(self.user, self.barcode1, now)

        results = TransactionQueryMixin.usage_over_time(
            granularity="day", since=now - timedelta(days=1)
        )
        self.assertGreaterEqual(len(results), 1)
        # At least one bucket with count 2
        total = sum(count for _, count in results)
        self.assertEqual(total, 2)

    def test_usage_over_time_invalid_granularity_raises(self):
        # Create at least one transaction so the scan has items to process
        now = timezone.now()
        self._create_tx(self.user, self.barcode1, now)

        with self.assertRaises(ValueError) as ctx:
            TransactionQueryMixin.usage_over_time(granularity="hour")
        self.assertIn("granularity", str(ctx.exception))

    def test_barcode_usage_stats_returns_correct_counts(self):
        now = timezone.now()
        self._create_tx(self.user, self.barcode1, now)
        self._create_tx(self.user, self.barcode1, now)
        self._create_tx(self.user, self.barcode2, now)

        stats = TransactionQueryMixin.barcode_usage_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["with_fk"], 3)
        self.assertEqual(stats["per_barcode"][self.barcode1["barcode_uuid"]], 2)
        self.assertEqual(stats["per_barcode"][self.barcode2["barcode_uuid"]], 1)

    def test_for_barcode_returns_filtered_transactions(self):
        now = timezone.now()
        tx1 = self._create_tx(self.user, self.barcode1, now)
        self._create_tx(self.user, self.barcode2, now)

        results = TransactionQueryMixin.for_barcode(self.barcode1["barcode_uuid"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sk"], tx1["sk"])

    def test_for_user_limit_bounds_result(self):
        now = timezone.now()
        for i in range(5):
            self._create_tx(self.user, self.barcode1, now - timedelta(minutes=i))

        results = TransactionRepository.for_user(self.user.id, limit=3)
        self.assertEqual(len(results), 3)
        # Ordering preserved (most recent first)
        times = [r["time_created"] for r in results]
        self.assertEqual(times, sorted(times, reverse=True))

    def test_for_user_no_limit_returns_all(self):
        now = timezone.now()
        for i in range(5):
            self._create_tx(self.user, self.barcode1, now - timedelta(minutes=i))

        results = TransactionRepository.for_user(self.user.id)
        self.assertEqual(len(results), 5)

    def test_for_barcode_limit_bounds_result(self):
        now = timezone.now()
        for i in range(5):
            self._create_tx(self.user, self.barcode1, now - timedelta(minutes=i))

        results = TransactionRepository.for_barcode(
            self.barcode1["barcode_uuid"], limit=2
        )
        self.assertEqual(len(results), 2)
        times = [r["time_created"] for r in results]
        self.assertEqual(times, sorted(times, reverse=True))

    def test_for_barcode_no_limit_returns_all(self):
        now = timezone.now()
        for i in range(5):
            self._create_tx(self.user, self.barcode1, now - timedelta(minutes=i))

        results = TransactionRepository.for_barcode(self.barcode1["barcode_uuid"])
        self.assertEqual(len(results), 5)


class TransactionRepositoryRoutingTests(TestCase):
    """
    Verify the bounded path uses query_limited and unbounded path uses
    query_all — guards against accidentally routing unlimited reads through
    the bounded helper (which would cap them at max_items).
    """

    def test_for_user_with_limit_routes_through_query_limited(self):
        with patch(
            "index.repositories.transaction_repo.query_limited",
            return_value=[],
        ) as mock_limited, patch(
            "index.repositories.transaction_repo.query_all",
            return_value=[],
        ) as mock_all:
            TransactionRepository.for_user(user_id=1, limit=5)

        mock_limited.assert_called_once()
        self.assertEqual(mock_limited.call_args.args[1], 5)
        mock_all.assert_not_called()

    def test_for_user_without_limit_routes_through_query_all(self):
        with patch(
            "index.repositories.transaction_repo.query_limited",
            return_value=[],
        ) as mock_limited, patch(
            "index.repositories.transaction_repo.query_all",
            return_value=[],
        ) as mock_all:
            TransactionRepository.for_user(user_id=1)

        mock_all.assert_called_once()
        mock_limited.assert_not_called()

    def test_for_barcode_with_limit_routes_through_query_limited(self):
        with patch(
            "index.repositories.transaction_repo.query_limited",
            return_value=[],
        ) as mock_limited, patch(
            "index.repositories.transaction_repo.query_all",
            return_value=[],
        ) as mock_all:
            TransactionRepository.for_barcode(barcode_uuid="bc", limit=3)

        mock_limited.assert_called_once()
        self.assertEqual(mock_limited.call_args.args[1], 3)
        mock_all.assert_not_called()

    def test_for_barcode_without_limit_routes_through_query_all(self):
        with patch(
            "index.repositories.transaction_repo.query_limited",
            return_value=[],
        ) as mock_limited, patch(
            "index.repositories.transaction_repo.query_all",
            return_value=[],
        ) as mock_all:
            TransactionRepository.for_barcode(barcode_uuid="bc")

        mock_all.assert_called_once()
        mock_limited.assert_not_called()


class TransactionServiceCompositeTests(TestCase):
    def test_service_inherits_both_mixins(self):
        self.assertTrue(hasattr(TransactionService, "create_transaction"))
        self.assertTrue(hasattr(TransactionService, "for_user"))
        self.assertTrue(hasattr(TransactionService, "top_barcodes"))
        self.assertTrue(hasattr(TransactionService, "bulk_ingest"))
