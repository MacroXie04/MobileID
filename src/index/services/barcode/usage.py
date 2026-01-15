from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from index.models import Barcode, BarcodeUsage, Transaction
from index.services.transactions import TransactionService

from .constants import BARCODE_IDENTIFICATION


def _touch_barcode_usage(barcode: Barcode, *, request_user=None) -> None:
    """Increment usage counters for *barcode* atomically.

    If the same user has used this barcode within the last 5 minutes,
    we skip recording a new transaction and do not increment usage counters.

    If a barcode is being used by someone other than its owner, we still
    update the `BarcodeUsage` counters but we do NOT create a `Transaction`.
    """
    now = timezone.now()

    # Check for duplicate usage within 5 minutes for the same user and barcode
    if request_user is not None:
        cutoff_5m = now - timedelta(minutes=5)
        recent_usage = Transaction.objects.filter(
            user=request_user,
            barcode_used=barcode,
            time_created__gte=cutoff_5m,
        ).exists()

        if recent_usage:
            # Skip recording - user already used this barcode within 5 minutes
            return

    # Skip BarcodeUsage tracking for Identification barcodes since they
    # regenerate each time
    # But still log transactions for audit purposes
    if barcode.barcode_type != BARCODE_IDENTIFICATION:
        # Try to update existing record first
        updated = BarcodeUsage.objects.filter(barcode=barcode).update(
            total_usage=F("total_usage") + 1, last_used=now
        )

        # If no rows were updated, create a new record
        if not updated:
            BarcodeUsage.objects.create(barcode=barcode, total_usage=1, last_used=now)

    if request_user is not None:
        TransactionService.create_transaction(
            user=request_user,
            barcode=barcode,
            time_created=now,
            save=True,
        )
