from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Final

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from mobileid.models import (
    Barcode,
    BarcodeUsage,
    UserAccount,
    UserBarcodeSettings,
)
from mobileid.project_code.barcode import auto_send_code
from barcode.settings import SELENIUM_ENABLED

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ACCOUNT_STAFF: Final[str] = "staff"
ACCOUNT_USER: Final[str] = "user"
ACCOUNT_SCHOOL: Final[str] = "school"

BARCODE_IDENTIFICATION: Final[str] = "Identification"
BARCODE_DYNAMIC: Final[str] = "DynamicBarcode"

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


def _select_least_used_dynamic_barcode() -> Barcode | None:
    """Return the least-used Dynamic barcode, or *None* if none exist."""
    qs = (
        BarcodeUsage.objects.select_related("barcode")
        .filter(barcode__barcode_type=BARCODE_DYNAMIC)
        .order_by("total_usage", "last_used")
    )
    return qs.first().barcode if qs.exists() else None


def _touch_barcode_usage(barcode: Barcode) -> None:
    """Increment usage counters for *barcode* atomically."""
    now = timezone.now()
    BarcodeUsage.objects.update_or_create(
        barcode=barcode, defaults={"last_used": now}
    )
    BarcodeUsage.objects.filter(barcode=barcode).update(
        total_usage=F("total_usage") + 1, last_used=now
    )


def _school_timestamp(randomised: bool) -> str:
    """Return a timestamp string for SCHOOL barcodes.

    * If *randomised* is False ⇒ current timestamp.
    * If True ⇒ random timestamp within the last 365 days.
    """
    now = timezone.now()
    if not randomised:
        return now.strftime("%Y%m%d%H%M%S")

    start = now - timedelta(days=365)
    seconds_offset = random.randint(0, int((now - start).total_seconds()))
    return (start + timedelta(seconds=seconds_offset)).strftime("%Y%m%d%H%M%S")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@transaction.atomic
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
            "barcode": _create_identification_barcode(user),
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

    # USER — always produce a new Identification barcode
    if account_type == ACCOUNT_USER:
        identification_barcode = _create_identification_barcode(user)
        settings.barcode = identification_barcode
        settings.save(update_fields=["barcode"])

        result.update(
            status="success",
            message="Identification barcode",
            barcode_type=BARCODE_IDENTIFICATION,
            barcode=identification_barcode.barcode,
        )
        return result

    # SCHOOL — uses Dynamic barcodes
    if account_type == ACCOUNT_SCHOOL:

        ts_prefix = _school_timestamp(randomised=not settings.timestamp_verification)

        # Pick existing Dynamic barcode or pull a new one
        if settings.barcode and settings.barcode.barcode_type == BARCODE_DYNAMIC:
            dynamic_barcode = settings.barcode
        else:
            settings.barcode_pull = True
            settings.save(update_fields=["barcode_pull"])
            dynamic_barcode = _select_least_used_dynamic_barcode()
            if dynamic_barcode is None:
                result.update(status="error", message="No dynamic barcode available")
                return result
            settings.barcode = dynamic_barcode
            settings.save(update_fields=["barcode"])

        # Update usage stats
        _touch_barcode_usage(dynamic_barcode)

        # Optional server verification
        server_note = ""
        if SELENIUM_ENABLED and settings.server_verification:
            srv = auto_send_code(dynamic_barcode.session)
            server_note = f" Server: {srv['code']}" if srv else ""

        full_barcode = f"{ts_prefix}{dynamic_barcode.barcode}"
        result.update(
            status="success",
            message=f"Dynamic: {dynamic_barcode.barcode[-4:]}{server_note}",
            barcode_type=BARCODE_DYNAMIC,
            barcode=full_barcode,
        )
        return result

    # Unknown account type
    result.update(message="Invalid account type.")
    return result
