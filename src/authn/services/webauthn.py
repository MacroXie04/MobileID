import random

from django.contrib.auth.models import Group

from authn.models import UserProfile
from index.models import Barcode, UserBarcodeSettings
from index.services.transactions import TransactionService


def generate_unique_information_id(length: int = 9) -> str:
    """Generate a unique numeric information_id of given length."""
    if length < 1:
        raise ValueError("length must be at least 1")

    lower = 10 ** (length - 1)
    upper = (10**length) - 1

    while True:
        info_id = str(random.randint(lower, upper))
        if not UserProfile.objects.filter(information_id=info_id).exists():
            return info_id


def generate_unique_identification_barcode():
    while True:
        code = "".join([str(random.randint(0, 9)) for _ in range(28)])
        if not Barcode.objects.filter(barcode=code).exists():
            return code


def create_user_profile(
    user, name: str, information_id: str | None, user_profile_img: str | None
):
    # Profile
    info_id = information_id or generate_unique_information_id()
    UserProfile.objects.create(
        user=user,
        name=name,
        information_id=info_id,
        # store NULL if empty
        user_profile_img=user_profile_img or None,
    )

    # Group membership  (creates "User" group if missing)
    user_group, _ = Group.objects.get_or_create(name="User")
    user.groups.add(user_group)

    # Identification barcode
    ident_barcode = Barcode.objects.create(
        user=user,
        barcode_type="Identification",
        barcode=generate_unique_identification_barcode(),
    )

    # Record transaction for identification barcode creation
    TransactionService.create_transaction(
        user=user,
        barcode=ident_barcode,
    )

    # Per‑user barcode settings
    UserBarcodeSettings.objects.create(
        user=user,
        barcode=ident_barcode,
        associate_user_profile_with_barcode=False,
    )

    return user
