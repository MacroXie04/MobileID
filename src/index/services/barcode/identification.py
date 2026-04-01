from index.repositories import BarcodeRepository

from .constants import BARCODE_IDENTIFICATION
from .utils import _random_digits


def generate_unique_identification_barcode(max_attempts: int = 50) -> str:
    """Return a unique 28-digit Identification barcode.

    Retries up to *max_attempts* before raising an exception.
    """
    for _ in range(max_attempts):
        code = _random_digits(28)
        if not BarcodeRepository.barcode_exists(code):
            return code
    raise RuntimeError(
        f"Unable to generate unique Identification barcode after "
        f"{max_attempts} attempts."
    )


def _carry_forward_identification_usage(
    old_barcodes: list[dict], new_barcode: dict
) -> None:
    """Merge prior Identification usage onto *new_barcode*."""
    if not old_barcodes:
        return

    total_usage = sum(int(b.get("total_usage", 0)) for b in old_barcodes)
    max_total_limit = max(int(b.get("total_usage_limit", 0)) for b in old_barcodes)
    max_daily_limit = max(int(b.get("daily_usage_limit", 0)) for b in old_barcodes)

    last_used_values = [b.get("last_used") for b in old_barcodes if b.get("last_used")]
    last_used = max(last_used_values) if last_used_values else None

    updates = {
        "total_usage": total_usage,
        "total_usage_limit": max_total_limit,
        "daily_usage_limit": max_daily_limit,
    }
    if last_used:
        updates["last_used"] = last_used

    BarcodeRepository.update(
        user_id=new_barcode["user_id"],
        barcode_uuid=new_barcode["barcode_uuid"],
        **updates,
    )


def _create_identification_barcode(user) -> dict:
    """Rotate a user's Identification barcode while preserving usage state."""
    old_barcodes = BarcodeRepository.get_user_barcodes_by_type(
        user.id, BARCODE_IDENTIFICATION
    )

    new_barcode = BarcodeRepository.create(
        user_id=user.id,
        barcode_value=generate_unique_identification_barcode(),
        barcode_type=BARCODE_IDENTIFICATION,
        owner_username=user.username,
    )

    if old_barcodes:
        _carry_forward_identification_usage(old_barcodes, new_barcode)
        for old_bc in old_barcodes:
            BarcodeRepository.delete(
                user_id=old_bc["user_id"],
                barcode_uuid=old_bc["barcode_uuid"],
            )

    return new_barcode
