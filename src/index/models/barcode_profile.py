from django.core.validators import MaxLengthValidator
from django.db import models


class BarcodeUserProfile(models.Model):
    # foreign key to barcode
    linked_barcode = models.OneToOneField("Barcode", on_delete=models.CASCADE)

    # user name and id
    name = models.CharField(max_length=100)
    information_id = models.CharField(max_length=100)

    # user profile image (base64 encoded png 128*128)
    user_profile_img = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "Base64 encoded PNG of the user's 128*128 avatar. " "No data-URI prefix."
        ),
        verbose_name="avatar (Base64)",
    )

    # user cookies
    user_cookies = models.TextField(null=True, blank=True)

    # gender
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Unknow", "Unknow"),
    ]
    gender_barcode = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Unknow")

