import secrets

from authn.models import UserProfile
from index.repositories import BarcodeRepository


def generate_unique_information_id(length: int = 9) -> str:
    """Generate a unique numeric information_id of given length."""
    if length < 1:
        raise ValueError("length must be at least 1")

    lower = 10 ** (length - 1)
    upper = (10**length) - 1

    while True:
        info_id = str(secrets.randbelow(upper - lower + 1) + lower)
        if not UserProfile.objects.filter(information_id=info_id).exists():
            return info_id


def generate_unique_identification_barcode() -> str:
    """Generate a unique 28-digit Identification barcode value."""
    while True:
        code = "".join(str(secrets.randbelow(10)) for _ in range(28))
        if not BarcodeRepository.barcode_exists(code):
            return code


__all__ = [
    "generate_unique_identification_barcode",
    "generate_unique_information_id",
]
