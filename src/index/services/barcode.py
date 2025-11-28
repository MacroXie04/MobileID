from __future__ import annotations

import random
from typing import Final

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from index.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
    UserBarcodePullSettings,
    Transaction,
)
from datetime import timedelta
from django.db.models import Q
from index.services.transactions import TransactionService
from index.services.usage_limit import UsageLimitService

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
        f"Unable to generate unique Identification barcode after "
        f"{max_attempts} attempts."
    )


def _create_identification_barcode(user) -> Barcode:
    """Delete prior Identification barcodes for *user* and create a fresh
    one."""
    Barcode.objects.filter(user=user, barcode_type=BARCODE_IDENTIFICATION).delete()
    return Barcode.objects.create(
        user=user,
        barcode_type=BARCODE_IDENTIFICATION,
        barcode=generate_unique_identification_barcode(),
    )


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


def _timestamp() -> str:
    """Return a timestamp string for dynamic barcodes."""
    return timezone.now().strftime("%Y%m%d%H%M%S")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_barcode(user) -> dict:
    """Generate or refresh a barcode for *user* based on their group
    membership."""
    result = RESULT_TEMPLATE.copy()

    # Determine account type via groups
    is_staff = user.groups.filter(name="Staff").exists()
    is_user = user.groups.filter(name="User").exists()
    is_school = user.groups.filter(name="School").exists()

    # STAFF — not allowed
    if is_staff:
        result.update(
            status="error", message="Staff accounts cannot generate barcodes."
        )
        return result

    # Unknown or missing group
    if not (is_user or is_school):
        result.update(status="error", message="Permission Denied.")
        return result

    # --------------------------------------------------------------
    # handle generate barcode

    # Wrap DB operations in an explicit transaction for select_for_update
    with transaction.atomic():
        (
            settings,
            _,
        ) = UserBarcodeSettings.objects.select_for_update().get_or_create(
            user=user,
            defaults={
                "barcode": None,
                "associate_user_profile_with_barcode": False,
            },
        )

        # handle barcode pull settings
        (
            pull_settings,
            _,
        ) = UserBarcodePullSettings.objects.select_for_update().get_or_create(
            user=user,
            defaults={
                "pull_setting": "Disable",
                "gender_setting": "Unknow",
            },
        )

        if (
            pull_settings.pull_setting == "Enable"
            and user.groups.filter(name="School").exists()
        ):
            # 1. Check for recent personal usage (Stickiness) - 10 min
            cutoff_10m = timezone.now() - timedelta(minutes=10)
            recent_txn = (
                Transaction.objects.filter(user=user, time_created__gte=cutoff_10m)
                .order_by("-time_created")
                .first()
            )

            candidate = None
            if recent_txn and recent_txn.barcode_used:
                candidate = recent_txn.barcode_used

            # 2. Pull from pool if no candidate
            if not candidate:
                cutoff_5m = timezone.now() - timedelta(minutes=5)

                # Base query: User's own barcodes OR Shareable Dynamic barcodes
                qs = Barcode.objects.filter(
                    Q(user=user)
                    | Q(share_with_others=True, barcode_type=BARCODE_DYNAMIC)
                )

                # Gender filter
                qs = qs.filter(
                    barcodeuserprofile__gender_barcode=pull_settings.gender_setting  # noqa: E501
                )

                # Usage filter: Exclude if used by ANYONE in last 5 mins
                qs = qs.exclude(barcodeusage__last_used__gte=cutoff_5m)

                # Pick one (randomly)
                if qs.exists():
                    candidate = qs.order_by("?").first()

            # 3. Apply selection
            if candidate:
                settings.barcode = candidate
                settings.save()

        # Use the user-selected barcode
        selected = settings.barcode

        # For User type, ensure they have an identification barcode
        if is_user:
            # Find or create their identification barcode
            ident_barcode = Barcode.objects.filter(
                user=user, barcode_type=BARCODE_IDENTIFICATION
            ).first()

            if not ident_barcode:
                # Create one if it doesn't exist
                ident_barcode = _create_identification_barcode(user)

            # Force the selection to identification barcode
            selected = ident_barcode
            settings.barcode = ident_barcode
            settings.associate_user_profile_with_barcode = False
            settings.save()

        if not selected:
            result.update(status="error", message="No barcode selected.")
            return result

        # Permission check:
        # - Users can always use their own barcodes
        # - For barcodes owned by others:
        #   * Only DynamicBarcode is eligible, and only if share_with_others=True  # noqa: E501
        if selected.user != user:
            if selected.barcode_type != BARCODE_DYNAMIC:
                result.update(status="error", message="Permission Denied.")
                return result
            if not getattr(selected, "share_with_others", False):
                result.update(status="error", message="Permission Denied.")
                return result

        # Handle by barcode type
        if selected.barcode_type == BARCODE_IDENTIFICATION:
            # Create fresh identification barcode
            new_bc = _create_identification_barcode(user)
            settings.barcode = new_bc
            settings.save(update_fields=["barcode"])

            # Check usage limits for the new barcode
            allowed, limit_error = UsageLimitService.check_all_limits(new_bc)
            if not allowed:
                result.update(status="error", message=limit_error)
                return result

            # Track usage for identification barcodes
            _touch_barcode_usage(new_bc, request_user=user)

            result.update(
                status="success",
                message="Identification barcode",
                barcode_type=BARCODE_IDENTIFICATION,
                barcode=new_bc.barcode,
            )
            return result

        if selected.barcode_type == BARCODE_DYNAMIC:
            # Check usage limits before generating
            allowed, limit_error = UsageLimitService.check_all_limits(selected)
            if not allowed:
                result.update(status="error", message=limit_error)
                return result

            # Update usage stats
            _touch_barcode_usage(selected, request_user=user)

            full = f"{_timestamp()}{selected.barcode}"
            result.update(
                status="success",
                message=f"Dynamic: {selected.barcode[-4:]}",
                barcode_type=BARCODE_DYNAMIC,
                barcode=full,
            )
            return result

        if selected.barcode_type == BARCODE_OTHERS:
            # Check usage limits before generating
            allowed, limit_error = UsageLimitService.check_all_limits(selected)
            if not allowed:
                result.update(status="error", message=limit_error)
                return result

            # Track usage for other barcode types
            _touch_barcode_usage(selected, request_user=user)

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
