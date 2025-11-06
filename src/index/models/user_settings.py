from django.contrib.auth.models import User
from django.db import models


# user barcode settings
class UserBarcodeSettings(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # barcode settings
    barcode = models.ForeignKey(
        "Barcode", on_delete=models.SET_NULL, blank=True, null=True
    )

    # server verification settings
    server_verification = models.BooleanField(default=False)

    # associate user profile with barcode
    associate_user_profile_with_barcode = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Barcode Settings"

