import secrets

from authn.models import UserProfile
from index.repositories import (  # noqa: F401
    BarcodeRepository,
    SettingsRepository,
    TransactionRepository,
)


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


def generate_unique_identification_barcode():
    while True:
        code = "".join([str(secrets.randbelow(10)) for _ in range(28)])
        if not BarcodeRepository.barcode_exists(code):
            return code


def create_user_profile(
    user, name: str, information_id: str | None, user_profile_img: str | None
):
    # Profile (stays in relational DB)
    info_id = information_id or generate_unique_information_id()
    UserProfile.objects.create(
        user=user,
        name=name,
        information_id=info_id,
        user_profile_img=user_profile_img or None,
    )

    # Identification barcode (DynamoDB)
    ident_barcode = BarcodeRepository.create(
        user_id=user.id,
        barcode_value=generate_unique_identification_barcode(),
        barcode_type="Identification",
        owner_username=user.username,
    )

    # Record transaction for identification barcode creation
    TransactionRepository.create(
        user_id=user.id,
        barcode_uuid=ident_barcode["barcode_uuid"],
        barcode_value=ident_barcode["barcode"],
    )

    # Per-user barcode settings
    SettingsRepository.update(
        user.id,
        active_barcode_uuid=ident_barcode["barcode_uuid"],
        associate_user_profile_with_barcode=False,
    )

    return user
