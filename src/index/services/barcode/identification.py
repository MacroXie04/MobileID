from django.db import transaction
from django.db.models import Max, Sum

from index.models import Barcode, BarcodeUsage

from .constants import BARCODE_IDENTIFICATION
from .utils import _random_digits


def generate_unique_identification_barcode(max_attempts: int = 50) -> str:
    """Return a unique 28-digit Identification barcode.

    Retries up to *max_attempts* before raising an exception.
    """
    for _ in range(max_attempts):
        code = _random_digits(28)
        if not Barcode.objects.filter(barcode=code).exists():
            return code
    raise RuntimeError(
        f"Unable to generate unique Identification barcode after "
        f"{max_attempts} attempts."
    )


def _carry_forward_identification_usage(
    old_barcode_ids: list[int], new_barcode: Barcode
) -> None:
    """Merge prior Identification usage rows onto *new_barcode*."""
    usage_rows = BarcodeUsage.objects.filter(barcode_id__in=old_barcode_ids)
    if not usage_rows.exists():
        return

    summary = usage_rows.aggregate(
        total_usage=Sum("total_usage"),
        total_usage_limit=Max("total_usage_limit"),
        daily_usage_limit=Max("daily_usage_limit"),
        last_used=Max("last_used"),
    )

    new_usage = BarcodeUsage.objects.create(
        barcode=new_barcode,
        total_usage=summary["total_usage"] or 0,
        total_usage_limit=summary["total_usage_limit"] or 0,
        daily_usage_limit=summary["daily_usage_limit"] or 0,
    )

    if summary["last_used"] is not None:
        # auto_now would overwrite a direct save(); keep the carried-forward
        # timestamp with a queryset update instead.
        BarcodeUsage.objects.filter(pk=new_usage.pk).update(
            last_used=summary["last_used"]
        )


def _create_identification_barcode(user) -> Barcode:
    """Rotate a user's Identification barcode while preserving usage state."""
    with transaction.atomic():
        old_barcode_ids = list(
            Barcode.objects.filter(
                user=user,
                barcode_type=BARCODE_IDENTIFICATION,
            ).values_list("pk", flat=True)
        )

        new_barcode = Barcode.objects.create(
            user=user,
            barcode_type=BARCODE_IDENTIFICATION,
            barcode=generate_unique_identification_barcode(),
        )

        if old_barcode_ids:
            _carry_forward_identification_usage(old_barcode_ids, new_barcode)
            Barcode.objects.filter(pk__in=old_barcode_ids).delete()

        return new_barcode
