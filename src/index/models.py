import uuid

from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator
from django.db import models


# barcode pull settings
class BarcodePullSettings(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # 


# barcode total usage
class BarcodeUsage(models.Model):
    # foreign key to barcode
    barcode = models.ForeignKey("Barcode", on_delete=models.CASCADE)

    # total usage count
    total_usage = models.PositiveIntegerField(default=0)

    # total usage limit
    total_usage_limit = models.PositiveIntegerField(default=0)

    # daily usage limit (0 means no limit)
    daily_usage_limit = models.PositiveIntegerField(default=0)

    # last used timestamp
    last_used = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Barcode ending with {self.barcode.barcode[-4:]} - Total Usage: {self.total_usage} - Last Used: {self.last_used}"


# barcode information
class Barcode(models.Model):
    # storage upload user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # timestamp of creation
    time_created = models.DateTimeField(auto_now_add=True, null=True, verbose_name="time created")

    # unique identifier for the barcode
    barcode_uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, null=True
    )

    # share with others option
    share_with_others = models.BooleanField(default=False)

    # barcode type (will be set up automatically)
    BARCODE_TYPE_CHOICES = [
        ("DynamicBarcode", "DynamicBarcode"),
        ("Identification", "Identification"),
        ("Others", "Others"),
    ]

    barcode_type = models.CharField(
        max_length=15,
        choices=BARCODE_TYPE_CHOICES,
        default="Others",
    )

    # barcode information
    barcode = models.CharField(max_length=120, unique=True)

    def __str__(self):
        if self.barcode_type == "DynamicBarcode":
            return f"Dynamic barcode ending with {self.barcode[-4:]}"
        elif self.barcode_type == "Identification":
            return f"{self.user.username}'s identification Barcode"
        return f"Barcode ending with {self.barcode[-4:]}"


class BarcodeUserProfile(models.Model):
    # foreign key to barcode
    linked_barcode = models.OneToOneField(Barcode, on_delete=models.CASCADE)

    # user name and id
    name = models.CharField(max_length=100)
    information_id = models.CharField(max_length=100)

    # user profile image (base64 encoded png 128*128)
    user_profile_img = models.TextField(
        null=True,
        blank=True,
        validators=[MaxLengthValidator(10_000)],
        help_text=(
            "Base64 encoded PNG of the user's 128*128 avatar. " "No data-URI prefix."
        ),
        verbose_name="avatar (Base64)",
    )

    # user cookies
    user_cookies = models.TextField(null=True, blank=True)


# user barcode settings
class UserBarcodeSettings(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # barcode settings
    barcode = models.ForeignKey(
        Barcode, on_delete=models.SET_NULL, blank=True, null=True
    )

    # server verification settings
    server_verification = models.BooleanField(default=False)

    # associate user profile with barcode
    associate_user_profile_with_barcode = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Barcode Settings"


class Transaction(models.Model):
    # foreign key to user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # usage detail
    barcode_used = models.ForeignKey(Barcode, default=None, on_delete=models.SET_NULL, null=True)
    time_created = models.DateTimeField(auto_now_add=True, null=True, verbose_name="time used")
