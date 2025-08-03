from __future__ import annotations

import random
from typing import Final

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from barcode.settings import SELENIUM_ENABLED
from mobileid.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
)
from mobileid.project_code.dynamic_barcode import auto_send_code

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BARCODE_IDENTIFICATION: Final[str] = "Identification"
BARCODE_DYNAMIC: Final[str] = "DynamicBarcode"
BARCODE_OTHERS: Final[str] = "Others"

RESULT_TEMPLATE = {
    "status": "error",  # overwritten on success
    "message": "Unexpected error",
    "barcode_type": None,
    "barcode": None,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _random_digits(length: int) -> str:
    """Return a random string of *length* numeric digits."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_unique_identification_barcode(max_attempts: int = 50) -> str:
    """Return a unique 28-digit Identification barcode.

    Retries up to *max_attempts* before raising an exception.
    """
    for _ in range(max_attempts):
        code = _random_digits(28)
        if not Barcode.objects.filter(barcode=code).exists():
            return code
    raise RuntimeError(
        f"Unable to generate unique Identification barcode after {max_attempts} attempts."
    )


def _create_identification_barcode(user) -> Barcode:
    """Delete prior Identification barcodes for *user* and create a fresh one."""
    Barcode.objects.filter(user=user, barcode_type=BARCODE_IDENTIFICATION).delete()
    return Barcode.objects.create(
        user=user,
        barcode_type=BARCODE_IDENTIFICATION,
        barcode=generate_unique_identification_barcode(),
    )


def _touch_barcode_usage(barcode: Barcode) -> None:
    """Increment usage counters for *barcode* atomically."""
    now = timezone.now()

    # Try to update existing record first
    updated = BarcodeUsage.objects.filter(barcode=barcode).update(
        total_usage=F("total_usage") + 1,
        last_used=now
    )

    # If no rows were updated, create a new record
    if not updated:
        BarcodeUsage.objects.create(
            barcode=barcode,
            total_usage=1,
            last_used=now
        )


def _select_optimal_dynamic_barcode() -> Barcode | None:
    """Select the optimal Dynamic barcode based on usage patterns."""
    dynamic_with_usage = (
        BarcodeUsage.objects.select_related("barcode")
        .filter(barcode__barcode_type=BARCODE_DYNAMIC)
        .order_by("total_usage", "last_used")
    )
    if dynamic_with_usage.exists():
        return dynamic_with_usage.first().barcode

    unused = (
        Barcode.objects.filter(barcode_type=BARCODE_DYNAMIC)
        .exclude(id__in=BarcodeUsage.objects.values_list("barcode_id", flat=True))
        .order_by("time_created")
    )
    return unused.first() if unused.exists() else None


def _timestamp() -> str:
    """Return a timestamp string for dynamic barcodes."""
    return timezone.now().strftime("%Y%m%d%H%M%S")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_barcode(user) -> dict:
    """Generate or refresh a barcode for *user* based on their group membership."""
    result = RESULT_TEMPLATE.copy()

    # Determine account type via groups
    is_staff = user.groups.filter(name="Staff").exists()
    is_user = user.groups.filter(name="User").exists()
    is_school = user.groups.filter(name="School").exists()

    # STAFF — not allowed
    if is_staff:
        result.update(status="error", message="Staff accounts cannot generate barcodes.")
        return result

    # Unknown or missing group
    if not (is_user or is_school):
        result.update(status="error", message="Invalid user group.")
        return result

    # Wrap DB operations in an explicit transaction for select_for_update
    with transaction.atomic():
        settings, _ = UserBarcodeSettings.objects.select_for_update().get_or_create(
            user=user,
            defaults={
                "barcode": None,
                "server_verification": False,
                "barcode_pull": False,
            },
        )

        # Determine which barcode to use
        if settings.barcode_pull and is_school:
            selected = _select_optimal_dynamic_barcode()
            if not selected:
                result.update(status="error", message="No dynamic barcode available for pull.")
                return result
        else:
            selected = settings.barcode

        if not selected:
            result.update(status="error", message="No barcode selected.")
            return result

        # Handle by barcode type
        if selected.barcode_type == BARCODE_IDENTIFICATION:
            # Create fresh identification barcode
            new_bc = _create_identification_barcode(user)
            settings.barcode = new_bc
            settings.save(update_fields=["barcode"])

            # Track usage for identification barcodes
            _touch_barcode_usage(new_bc)

            result.update(
                status="success",
                message="Identification barcode",
                barcode_type=BARCODE_IDENTIFICATION,
                barcode=new_bc.barcode,
            )
            return result

        if selected.barcode_type == BARCODE_DYNAMIC:
            # Update usage stats
            _touch_barcode_usage(selected)

            # Optional server verification
            server_note = ""
            if SELENIUM_ENABLED and settings.server_verification:
                srv = auto_send_code(selected.session)
                server_note = f" Server: {srv['code']}" if srv else ""

            full = f"{_timestamp()}{selected.barcode}"
            result.update(
                status="success",
                message=f"Dynamic: {selected.barcode[-4:]}{server_note}",
                barcode_type=BARCODE_DYNAMIC,
                barcode=full,
            )
            return result

        if selected.barcode_type == BARCODE_OTHERS:
            # Track usage for other barcode types
            _touch_barcode_usage(selected)

            result.update(
                status="success",
                message=f"Barcode ending with {selected.barcode[-4:]}",
                barcode_type=BARCODE_OTHERS,
                barcode=selected.barcode,
            )
            return result

        # Fallback error
        result.update(status="error", message="Invalid barcode type.")
        return result