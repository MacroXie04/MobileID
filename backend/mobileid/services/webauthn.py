import random

from mobileid.models import UserProfile, UserBarcodeSettings, UserAccount, Barcode


def generate_unique_identification_barcode():
    while True:
        code = ''.join([str(random.randint(0, 9)) for _ in range(28)])
        if not Barcode.objects.filter(barcode=code).exists():
            return code


def create_user_profile(user, name, information_id, user_profile_img):
    # Create a user profile with the provided details
    UserProfile.objects.create(
        user=user,
        name=name,
        information_id=information_id,
        user_profile_img=user_profile_img,
    )

    # Create a user account with the default settings
    UserAccount.objects.create(
        user=user,
        # Default account type
        account_type="User",
    )

    # Create user identification barcode
    user_identification_barcode = Barcode.objects.create(
        user=user,
        barcode_type="Identification",
        barcode=generate_unique_identification_barcode(),
    )

    # Create user barcode settings
    UserBarcodeSettings.objects.create(
        user=user,
        barcode=user_identification_barcode,
        server_verification=False,
        barcode_pull=False,
    )

    return user
