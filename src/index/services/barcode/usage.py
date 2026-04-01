from datetime import timedelta

from django.utils import timezone

from index.repositories import BarcodeRepository, TransactionRepository

from .constants import BARCODE_IDENTIFICATION, USAGE_COOLDOWN_MINUTES


def _has_recent_duplicate_usage(
    barcode: dict,
    *,
    request_user,
    cutoff_5m: str,
) -> bool:
    """Return True when usage should be suppressed by the cooldown window."""
    if barcode.get("barcode_type") == BARCODE_IDENTIFICATION:
        last_used = barcode.get("last_used")
        return bool(last_used and last_used >= cutoff_5m)

    return TransactionRepository.recent_user_barcode_usage(
        user_id=request_user.id,
        barcode_uuid=barcode["barcode_uuid"],
        since=cutoff_5m,
    )


def _touch_barcode_usage(barcode: dict, *, request_user=None) -> None:
    """Increment usage counters for *barcode* atomically.

    If the same user has used this barcode within the last 5 minutes,
    we skip recording a new transaction and do not increment usage counters.

    If a barcode is being used by someone other than its owner, we still
    update the usage counters but we do NOT create a Transaction.
    """
    now = timezone.now()

    # Check for duplicate usage within 5 minutes for the same user and barcode
    if request_user is not None:
        cutoff_5m = (now - timedelta(minutes=USAGE_COOLDOWN_MINUTES)).isoformat()
        if _has_recent_duplicate_usage(
            barcode,
            request_user=request_user,
            cutoff_5m=cutoff_5m,
        ):
            return

    # Atomic increment: total_usage += 1, last_used = now
    BarcodeRepository.increment_usage(
        user_id=barcode["user_id"],
        barcode_uuid=barcode["barcode_uuid"],
    )

    if request_user is not None:
        TransactionRepository.create(
            user_id=request_user.id,
            barcode_uuid=barcode["barcode_uuid"],
            barcode_value=barcode.get("barcode"),
            time_created=now.isoformat(),
        )
