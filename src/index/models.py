import uuid

from django.contrib.auth.models import User
from django.db import models


# barcode total usage
class BarcodeUsage(models.Model):
    # foreign key to barcode
    barcode = models.ForeignKey("Barcode", on_delete=models.CASCADE)

    # total usage count
    total_usage = models.PositiveIntegerField(default=0)

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

    # barcode pull settings
    barcode_pull = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Barcode Settings"


class DynamicBarcodeAddon(models.Model):
    # foreign key to barcode
    barcode = models.ForeignKey(Barcode, on_delete=models.CASCADE)

    # server verification information
    session = models.TextField(blank=True, null=True)

    # User Account Data
    user_name = models.CharField(max_length=100, blank=True, null=True)
    user_id = models.CharField(max_length=100, blank=True, null=True)
    userprofile_img = models.TextField(
        null=True,
        blank=True,
        help_text="Base64 encoded PNG of the user's 128*128 avatar. No data-URI prefix.",
        verbose_name="avatar (Base64)",
    )

    def __str__(self):
        return f"{self.addon_type} for {self.barcode.barcode} - Data: {self.addon_data[:20]}..."
