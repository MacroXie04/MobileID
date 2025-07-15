from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Final, Literal

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
    "status": "error",  # default until overwritten
    "message": "Unexpected error",
    "barcode_type": None,
    "barcode": None,
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _generate_random_digits(length: int) -> str:
    """Return a random string of *length* numeric digits."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_unique_identification_barcode(max_attempts: int = 50) -> str:
    """Return a unique 28-digit barcode, retrying up to *max_attempts* times."""
    for _ in range(max_attempts):
        code = _generate_random_digits(28)
        if not Barcode.objects.filter(barcode=code).exists():
            return code
    raise RuntimeError("Unable to generate unique identification barcode after"
                       f" {max_attempts} attempts.")


def _create_identification_barcode(user) -> Barcode:
    """Create and return a fresh identification barcode for *user*."""
    return Barcode.objects.create(
        user=user,
        barcode_type=BARCODE_IDENTIFICATION,
        barcode=generate_unique_identification_barcode(),
    )


def _select_least_used_dynamic_barcode() -> Barcode | None:
    """Return the least-used dynamic barcode (or *None* if none exist)."""
    usage_qs = (
        BarcodeUsage.objects.select_related("barcode")
        .filter(barcode__barcode_type=BARCODE_DYNAMIC)
        .order_by("total_usage", "last_used")
    )
    return usage_qs.first().barcode if usage_qs.exists() else None


def _touch_barcode_usage(barcode: Barcode) -> None:
    """Increment *barcode* usage counters atomically."""
    now = timezone.now()
    BarcodeUsage.objects.update_or_create(
        barcode=barcode,
        defaults={"last_used": now},
    )
    BarcodeUsage.objects.filter(barcode=barcode).update(
        total_usage=F("total_usage") + 1, last_used=now
    )


def _timestamp_for_school(randomised: bool) -> str:
    """Return a timestamp string for school barcodes.

    If *randomised* is *True*, generate a random timestamp within the past year.
    Otherwise, use *now*.
    """
    tz = timezone.get_current_timezone()
    now = timezone.now().astimezone(tz)

    if randomised:
        start = now - timedelta(days=365)
        seconds_offset = random.randint(0, int((now - start).total_seconds()))
        ts = (start + timedelta(seconds=seconds_offset)).strftime("%Y%m%d%H%M%S")
    else:
        ts = now.strftime("%Y%m%d%H%M%S")
    return ts

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@transaction.atomic
def generate_barcode(user) -> dict:
    """Generate or retrieve a barcode for *user* based on their account type.

    Returns a dict with keys: ``status``, ``message``, ``barcode_type``,
    ``barcode``. The function is fully transactional to guarantee consistency
    even under concurrent access.
    """
    result = RESULT_TEMPLATE.copy()

    # 1. Ensure the user has an account object.
    user_account, _ = UserAccount.objects.get_or_create(
        user=user, defaults={"account_type": ACCOUNT_USER.capitalize()}
    )
    account_type = user_account.account_type.lower()

    # 2. Ensure the user has settings (and identification barcode if missing).
    settings, _ = UserBarcodeSettings.objects.select_for_update().get_or_create(
        user=user,
        defaults={
            "barcode": _create_identification_barcode(user),
            "server_verification": False,
            "barcode_pull": False,
        },
    )

    # ---------------------------------------------------------------------
    # Branch per account type
    # ---------------------------------------------------------------------

    # --- STAFF -----------------------------------------------------------
    if account_type == ACCOUNT_STAFF:
        result.update(
            status="error",
            message="Staff accounts cannot generate barcodes.",
        )
        return result

    # --- USER ------------------------------------------------------------
    if account_type == ACCOUNT_USER:
        # Replace existing identification barcode with a new one.
        Barcode.objects.filter(user=user, barcode_type=BARCODE_IDENTIFICATION).delete()
        identification_barcode = _create_identification_barcode(user)
        settings.barcode = identification_barcode
        settings.save(update_fields=["barcode"])

        result.update(
            status="success",
            message="Identification barcode generated successfully.",
            barcode_type=BARCODE_IDENTIFICATION,
            barcode=identification_barcode.barcode,
        )
        return result

    # --- SCHOOL ----------------------------------------------------------
    if account_type == ACCOUNT_SCHOOL:
        # 1. Determine timestamp prefix.
        ts_prefix = _timestamp_for_school(randomised=not settings.timestamp_verification)

        # 2. Select or pull a dynamic barcode.
        if settings.barcode and settings.barcode.barcode_type == BARCODE_DYNAMIC:
            dynamic_barcode = settings.barcode
        else:
            settings.barcode_pull = True
            settings.save(update_fields=["barcode_pull"])
            dynamic_barcode = _select_least_used_dynamic_barcode()
            if dynamic_barcode is None:
                result.update(
                    status="error",
                    message="No dynamic barcode available.",
                )
                return result
            # Track that this user now owns this barcode (optional business rule)
            settings.barcode = dynamic_barcode
            settings.save(update_fields=["barcode"])

        # 3. Update usage statistics.
        _touch_barcode_usage(dynamic_barcode)

        # 4. Optional server verification.
        server_msg = ""
        if SELENIUM_ENABLED and settings.server_verification:
            srv_res = auto_send_code(dynamic_barcode.session)
            server_msg = f" Server: {srv_res['code']}" if srv_res else ""

        # 5. Compose result.
        full_barcode = f"{ts_prefix}{dynamic_barcode.barcode}"
        result.update(
            status="success",
            message=f"Dynamic: {dynamic_barcode.barcode[-4:]}{server_msg}",
            barcode_type=BARCODE_DYNAMIC,
            barcode=full_barcode,
        )
        return result

    # --- Unknown account type -------------------------------------------
    result.update(message="Invalid account type.")
    return result
