import random

from src.authn.models import UserProfile
from django.contrib.auth.models import Group
from src.index.models import UserBarcodeSettings, Barcode
from src.index.services.transactions import TransactionService


def generate_unique_identification_barcode():
    while True:
        code = "".join([str(random.randint(0, 9)) for _ in range(28)])
        if not Barcode.objects.filter(barcode=code).exists():
            return code


def create_user_profile(
        user, name: str, information_id: str, user_profile_img: str | None
):
    # Profile
    UserProfile.objects.create(
        user=user,
        name=name,
        information_id=information_id,
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
        server_verification=False,
        associate_user_profile_with_barcode=False,
    )

    return user
