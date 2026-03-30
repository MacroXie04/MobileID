from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.utils import timezone

from index.models import Barcode, Transaction
from index.services.transactions import TransactionService
from index.services.transaction_writes import TransactionWriteMixin, CreatedTransaction
from index.services.transaction_queries import TransactionQueryMixin


class TransactionWriteServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="txwriter", password="pass123")
        cls.barcode = Barcode.objects.create(
            user=cls.user, barcode="1234567890123456", barcode_type="DynamicBarcode"
        )

    def test_create_transaction_success(self):
        tx = TransactionWriteMixin.create_transaction(
            user=self.user, barcode=self.barcode
        )
        self.assertIsNotNone(tx.pk)
        self.assertEqual(tx.user, self.user)
        self.assertEqual(tx.barcode_used, self.barcode)

    def test_create_transaction_requires_barcode(self):
        with self.assertRaises(ValueError) as ctx:
            TransactionWriteMixin.create_transaction(user=self.user, barcode=None)
        self.assertIn("barcode", str(ctx.exception).lower())

    def test_create_transaction_rejects_non_barcode_instance(self):
        with self.assertRaises(ValueError):
            TransactionWriteMixin.create_transaction(
                user=self.user, barcode="not-a-barcode"
            )

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

    def test_create_transaction_save_false(self):
        tx = TransactionWriteMixin.create_transaction(
            user=self.user, barcode=self.barcode, save=False
        )
        self.assertIsNone(tx.pk)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 0)

    def test_bulk_ingest_success(self):
        user2 = User.objects.create_user(username="txwriter2", password="pass123")
        barcode2 = Barcode.objects.create(
            user=user2, barcode="9876543210123456", barcode_type="Others"
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


class TransactionQueryServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="txreader", password="pass123")
        cls.user2 = User.objects.create_user(username="txreader2", password="pass123")
        cls.barcode1 = Barcode.objects.create(
            user=cls.user, barcode="1111111111111111", barcode_type="DynamicBarcode"
        )
        cls.barcode2 = Barcode.objects.create(
            user=cls.user, barcode="2222222222222222", barcode_type="Others"
        )

    def setUp(self):
        Transaction.objects.all().delete()

    def _create_tx(self, user, barcode, time_created=None):
        """Create a transaction, optionally overriding auto_now_add timestamp."""
        tx = Transaction.objects.create(user=user, barcode_used=barcode)
        if time_created:
            # auto_now_add prevents direct assignment, so use queryset update
            Transaction.objects.filter(pk=tx.pk).update(time_created=time_created)
            tx.refresh_from_db()
        return tx

    def test_for_user_returns_ordered_transactions(self):
        now = timezone.now()
        tx1 = self._create_tx(self.user, self.barcode1, now - timedelta(hours=2))
        tx2 = self._create_tx(self.user, self.barcode1, now - timedelta(hours=1))
        # Other user's transaction should not appear
        self._create_tx(self.user2, self.barcode2, now)

        results = list(TransactionQueryMixin.for_user(self.user))
        self.assertEqual(len(results), 2)
        # Most recent first
        self.assertEqual(results[0].pk, tx2.pk)
        self.assertEqual(results[1].pk, tx1.pk)

    def test_for_user_with_since_filter(self):
        now = timezone.now()
        self._create_tx(self.user, self.barcode1, now - timedelta(days=2))
        tx_recent = self._create_tx(self.user, self.barcode1, now - timedelta(hours=1))

        results = list(
            TransactionQueryMixin.for_user(self.user, since=now - timedelta(days=1))
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, tx_recent.pk)

    def test_for_user_with_until_filter(self):
        now = timezone.now()
        tx_old = self._create_tx(self.user, self.barcode1, now - timedelta(days=2))
        self._create_tx(self.user, self.barcode1, now - timedelta(hours=1))

        results = list(
            TransactionQueryMixin.for_user(self.user, until=now - timedelta(days=1))
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, tx_old.pk)

    def test_top_barcodes_returns_ranked_list(self):
        now = timezone.now()
        # barcode1 used 3 times, barcode2 used 1 time
        for i in range(3):
            self._create_tx(self.user, self.barcode1, now - timedelta(minutes=i))
        self._create_tx(self.user, self.barcode2, now)

        results = TransactionQueryMixin.top_barcodes()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], self.barcode1.pk)
        self.assertEqual(results[0][1], 3)
        self.assertEqual(results[1][0], self.barcode2.pk)
        self.assertEqual(results[1][1], 1)

    def test_top_barcodes_with_limit(self):
        now = timezone.now()
        for i in range(3):
            self._create_tx(self.user, self.barcode1, now - timedelta(minutes=i))
        self._create_tx(self.user, self.barcode2, now)

        results = TransactionQueryMixin.top_barcodes(limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], self.barcode1.pk)

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
        self.assertEqual(stats["per_barcode"][str(self.barcode1.pk)], 2)
        self.assertEqual(stats["per_barcode"][str(self.barcode2.pk)], 1)

    def test_for_barcode_returns_filtered_transactions(self):
        now = timezone.now()
        tx1 = self._create_tx(self.user, self.barcode1, now)
        self._create_tx(self.user, self.barcode2, now)

        results = list(TransactionQueryMixin.for_barcode(self.barcode1))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, tx1.pk)


class TransactionServiceCompositeTests(TestCase):
    def test_service_inherits_both_mixins(self):
        self.assertTrue(hasattr(TransactionService, "create_transaction"))
        self.assertTrue(hasattr(TransactionService, "for_user"))
        self.assertTrue(hasattr(TransactionService, "top_barcodes"))
        self.assertTrue(hasattr(TransactionService, "bulk_ingest"))
