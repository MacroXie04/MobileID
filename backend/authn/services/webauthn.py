import random

from mobileid.models import UserBarcodeSettings, Barcode
from authn.models import UserProfile

from django.contrib.auth.models import Group

def generate_unique_identification_barcode():
    while True:
        code = ''.join([str(random.randint(0, 9)) for _ in range(28)])
        if not Barcode.objects.filter(barcode=code).exists():
            return code


def create_user_profile(user, name: str, information_id: str, user_profile_img: str | None):
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

    # Per‑user barcode settings
    UserBarcodeSettings.objects.create(
        user=user,
        barcode=ident_barcode,
        server_verification=False,
        barcode_pull=False,
    )

    return user
