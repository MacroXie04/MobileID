from authn.models import UserProfile
from index.repositories import (
    BarcodeRepository,
    SettingsRepository,
    TransactionRepository,
)

from .identifiers import (
    generate_unique_identification_barcode,
    generate_unique_information_id,
)


def create_user_profile(
    user, name: str, information_id: str | None, user_profile_img: str | None
):
    """Create the relational profile plus the default Identification barcode."""
    info_id = information_id or generate_unique_information_id()
    UserProfile.objects.create(
        user=user,
        name=name,
        information_id=info_id,
        user_profile_img=user_profile_img or None,
    )

    ident_barcode = BarcodeRepository.create(
        user_id=user.id,
        barcode_value=generate_unique_identification_barcode(),
        barcode_type="Identification",
        owner_username=user.username,
    )

    TransactionRepository.create(
        user_id=user.id,
        barcode_uuid=ident_barcode["barcode_uuid"],
        barcode_value=ident_barcode["barcode"],
    )

    SettingsRepository.update(
        user.id,
        active_barcode_uuid=ident_barcode["barcode_uuid"],
        associate_user_profile_with_barcode=False,
    )

    return user


__all__ = ["create_user_profile"]
