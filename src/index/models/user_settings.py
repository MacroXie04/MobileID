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

    class Meta:
        app_label = "index"

    def __str__(self):
        return f"{self.user.username}'s Barcode Settings"


class UserBarcodePullSettings(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # barcode pull settings
    PULL_CHOICES = [
        ("Enable", "Enable"),
        ("Disable", "Disable"),
    ]
    pull_setting = models.CharField(
        max_length=10, choices=PULL_CHOICES, default="Disable"
    )

    # Barcode pull gender choices
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Unknow", "Unknow"),
    ]

    gender_setting = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default="Unknow"
    )

    class Meta:
        app_label = "index"

    def __str__(self):
        return f"{self.user.username}'s Barcode Pull Settings"
