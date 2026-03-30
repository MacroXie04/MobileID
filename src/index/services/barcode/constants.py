from typing import Final

BARCODE_IDENTIFICATION: Final[str] = "Identification"
BARCODE_DYNAMIC: Final[str] = "DynamicBarcode"
BARCODE_OTHERS: Final[str] = "Others"

STICKINESS_MINUTES: Final[int] = 10
USAGE_COOLDOWN_MINUTES: Final[int] = 5

RESULT_TEMPLATE = {
    "status": "error",  # overwritten on success
    "message": "Unexpected error",
    "barcode_type": None,
    "barcode": None,
}
