from datetime import timedelta

from django.utils import timezone

from index.repositories import (
    BarcodeRepository,
    SettingsRepository,
    TransactionRepository,
)
from index.repositories.barcode_repo import (
    PULL_CANDIDATE_LIMIT,
    SHARED_DYNAMIC_QUERY_PAGE_SIZE,
)
from index.services.usage_limit import UsageLimitService

from .constants import (
    BARCODE_DYNAMIC,
    BARCODE_IDENTIFICATION,
    BARCODE_OTHERS,
    RESULT_TEMPLATE,
    STICKINESS_MINUTES,
    USAGE_COOLDOWN_MINUTES,
)
from .identification import _create_identification_barcode
from .usage import _touch_barcode_usage
from .utils import _timestamp


def generate_barcode(user) -> dict:
    """Generate or refresh a barcode for *user*."""
    result = RESULT_TEMPLATE.copy()
    selected = None

    settings = SettingsRepository.get_or_create(user.id)

    if settings.get("pull_setting") == "Enable":
        # 1. Check for recent personal usage (Stickiness)
        cutoff_10m = (
            timezone.now() - timedelta(minutes=STICKINESS_MINUTES)
        ).isoformat()
        recent_txn = TransactionRepository.recent_user_usage(user.id, since=cutoff_10m)

        candidate = None
        if recent_txn and recent_txn.get("barcode_uuid"):
            bc_uuid = recent_txn["barcode_uuid"]
            # Look up the barcode to get full data
            user_barcodes = BarcodeRepository.get_user_barcodes(user.id)
            candidate = next(
                (b for b in user_barcodes if b["barcode_uuid"] == bc_uuid), None
            )
            if not candidate:
                # Might be a shared barcode from another user
                candidate = BarcodeRepository.get_by_barcode_value(
                    recent_txn.get("barcode_value", "")
                )

        # 2. Pull from pool if no candidate
        if not candidate:
            cutoff_5m = (
                timezone.now() - timedelta(minutes=USAGE_COOLDOWN_MINUTES)
            ).isoformat()

            candidates = BarcodeRepository.get_pull_candidates(
                gender_setting=settings.get("pull_gender_setting", "Unknow"),
                exclude_user_id=user.id,
                cooldown_cutoff=cutoff_5m,
                limit=PULL_CANDIDATE_LIMIT,
                page_size=SHARED_DYNAMIC_QUERY_PAGE_SIZE,
            )

            if candidates:
                import random

                candidate = random.choice(candidates)

        # 3. Apply selection
        if candidate:
            SettingsRepository.set_active_barcode(
                user.id,
                candidate["barcode_uuid"],
                owner_user_id=candidate.get("user_id"),
            )
            settings["active_barcode_uuid"] = candidate["barcode_uuid"]
            settings["active_barcode_owner_id"] = str(candidate.get("user_id"))
            selected = candidate

    # Use the user-selected barcode
    active_uuid = settings.get("active_barcode_uuid")

    if not active_uuid:
        result.update(status="error", message="No barcode selected.")
        return result

    # Look up the selected barcode unless pull logic already selected it.
    if selected and selected.get("barcode_uuid") != active_uuid:
        selected = None

    if not selected:
        selected = SettingsRepository.get_active_barcode(user.id, settings)

    if not selected:
        result.update(status="error", message="No barcode selected.")
        return result

    # Permission check
    if selected["user_id"] != str(user.id):
        if selected.get("barcode_type") != BARCODE_DYNAMIC:
            result.update(status="error", message="Permission Denied.")
            return result
        if not selected.get("share_with_others", False):
            result.update(status="error", message="Permission Denied.")
            return result

    barcode_type = selected.get("barcode_type")

    # Handle by barcode type
    if barcode_type == BARCODE_IDENTIFICATION:
        new_bc = _create_identification_barcode(user)
        SettingsRepository.set_active_barcode(user.id, new_bc["barcode_uuid"])

        allowed, limit_error = UsageLimitService.check_all_limits(new_bc)
        if not allowed:
            result.update(status="error", message=limit_error)
            return result

        _touch_barcode_usage(new_bc, request_user=user)

        result.update(
            status="success",
            message="Identification barcode",
            barcode_type=BARCODE_IDENTIFICATION,
            barcode=new_bc["barcode"],
        )
        return result

    if barcode_type == BARCODE_DYNAMIC:
        allowed, limit_error = UsageLimitService.check_all_limits(selected)
        if not allowed:
            result.update(status="error", message=limit_error)
            return result

        _touch_barcode_usage(selected, request_user=user)

        full = f"{_timestamp()}{selected['barcode']}"
        result.update(
            status="success",
            message=f"Dynamic: {selected['barcode'][-4:]}",
            barcode_type=BARCODE_DYNAMIC,
            barcode=full,
        )
        return result

    if barcode_type == BARCODE_OTHERS:
        allowed, limit_error = UsageLimitService.check_all_limits(selected)
        if not allowed:
            result.update(status="error", message=limit_error)
            return result

        _touch_barcode_usage(selected, request_user=user)

        result.update(
            status="success",
            message=f"Barcode ending with {selected['barcode'][-4:]}",
            barcode_type=BARCODE_OTHERS,
            barcode=selected["barcode"],
        )
        return result

    result.update(status="error", message="Invalid barcode type.")
    return result
