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

from authn.models import UserAccount

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ACCOUNT_STAFF: Final[str] = "staff"
ACCOUNT_USER: Final[str] = "user"
ACCOUNT_SCHOOL: Final[str] = "school"

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
    # Ensure only one Identification barcode remains per user
    Barcode.objects.filter(user=user, barcode_type=BARCODE_IDENTIFICATION).delete()
    return Barcode.objects.create(
        user=user,
        barcode_type=BARCODE_IDENTIFICATION,
        barcode=generate_unique_identification_barcode(),
    )


def _touch_barcode_usage(barcode: Barcode) -> None:
    """Increment usage counters for *barcode* atomically."""
    now = timezone.now()
    BarcodeUsage.objects.update_or_create(
        barcode=barcode, defaults={"last_used": now}
    )
    BarcodeUsage.objects.filter(barcode=barcode).update(
        total_usage=F("total_usage") + 1, last_used=now
    )


def _select_optimal_dynamic_barcode() -> Barcode | None:
    """Select the optimal Dynamic barcode based on usage patterns.

    Selection criteria (in order of priority):
    1. Never used barcodes (total_usage = 0)
    2. Least used barcodes (lowest total_usage)
    3. Among equally used barcodes, select the one used longest ago (oldest last_used)

    Returns:
        Barcode | None: The selected barcode, or None if no dynamic barcodes exist.
    """
    # Get all dynamic barcodes with their usage stats
    dynamic_barcodes_with_usage = (
        BarcodeUsage.objects.select_related("barcode")
        .filter(barcode__barcode_type=BARCODE_DYNAMIC)
        .order_by("total_usage", "last_used")
    )

    if not dynamic_barcodes_with_usage.exists():
        # Check if there are dynamic barcodes without usage records
        unused_dynamic_barcodes = (
            Barcode.objects.filter(barcode_type=BARCODE_DYNAMIC)
            .exclude(id__in=BarcodeUsage.objects.values_list("barcode_id", flat=True))
        )

        if unused_dynamic_barcodes.exists():
            # Return the first unused barcode (could be ordered by creation time)
            return unused_dynamic_barcodes.order_by("time_created").first()

        return None

    # Return the barcode with optimal usage pattern
    return dynamic_barcodes_with_usage.first().barcode


def _timestamp() -> str:
    """Return a timestamp string for dynamic barcodes."""
    now = timezone.now()
    return now.strftime("%Y%m%d%H%M%S")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# MySQL does not support nested transactions
# @transaction.atomic
def generate_barcode(user) -> dict:
    """Generate or refresh a barcode for *user* based on their account type.

    Always returns a dict with keys: ``status``, ``message``, ``barcode_type``,
    ``barcode``.
    """
    result = RESULT_TEMPLATE.copy()

    # ---------------------------------------------------------------------
    # 1 – Ensure prerequisite objects exist
    # ---------------------------------------------------------------------
    user_account, _ = UserAccount.objects.get_or_create(
        user=user, defaults={"account_type": ACCOUNT_USER.capitalize()}
    )
    account_type = user_account.account_type.lower()

    settings, created = UserBarcodeSettings.objects.select_for_update().get_or_create(
        user=user,
        defaults={
            "barcode": None,
            "server_verification": False,
            "barcode_pull": False,
        },
    )

    # ---------------------------------------------------------------------
    # 2 – Branch per account type
    # ---------------------------------------------------------------------

    # STAFF — not allowed
    if account_type == ACCOUNT_STAFF:
        result.update(status="error", message="Staff accounts cannot generate barcodes.")
        return result

    # USER and SCHOOL — both return their selected barcode
    if account_type in [ACCOUNT_USER, ACCOUNT_SCHOOL]:

        # init selected_barcode
        selected_barcode = None

        # process barcode_pull logic (only for School accounts)
        if settings.barcode_pull and account_type == ACCOUNT_SCHOOL:
            # try to get the optimal dynamic barcode
            pulled_barcode = _select_optimal_dynamic_barcode()
            if pulled_barcode:
                selected_barcode = pulled_barcode
            else:
                result.update(status="error", message="No dynamic barcode available for pull.")
                return result
        else:
            # use user-selected barcode
            selected_barcode = settings.barcode

        # check if there is a usable barcode
        if not selected_barcode:
            if account_type == ACCOUNT_SCHOOL:
                result.update(status="error",
                              message="No barcode selected.")
            else:
                result.update(status="error", message="No barcode selected.")
            return result

        # Handle different barcode types
        if selected_barcode.barcode_type == BARCODE_IDENTIFICATION:

            result.update(
                status="success",
                message="Identification barcode",
                barcode_type=BARCODE_IDENTIFICATION,
                barcode=selected_barcode.barcode,
            )
            return result

        elif selected_barcode.barcode_type == BARCODE_DYNAMIC:
            # Add timestamp prefix for dynamic barcodes
            ts_prefix = _timestamp()

            # Update usage stats
            _touch_barcode_usage(selected_barcode)

            # Optional server verification
            server_note = ""
            if SELENIUM_ENABLED and settings.server_verification:
                srv = auto_send_code(selected_barcode.session)
                server_note = f" Server: {srv['code']}" if srv else ""

            full_barcode = f"{ts_prefix}{selected_barcode.barcode}"
            result.update(
                status="success",
                message=f"Dynamic: {selected_barcode.barcode[-4:]}{server_note}",
                barcode_type=BARCODE_DYNAMIC,
                barcode=full_barcode,
            )
            return result

        elif selected_barcode.barcode_type == BARCODE_OTHERS:

            result.update(
                status="success",
                message=f"Barcode ending with {selected_barcode.barcode[-4:]}",
                barcode_type=BARCODE_OTHERS,
                barcode=selected_barcode.barcode,
            )
            return result

        else:
            result.update(status="error", message="Invalid barcode type.")
            return result

    # Unknown account type
    result.update(message="Invalid account type.")
    return result
