from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import uuid, time

class UserAccount(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # account verification
    account_verification = models.BooleanField(default=False)

    # user account type settings
    ACCOUNT_TYPE_CHOICES = [
        ("School", "School"),
        ("Student", "Student"),
        ("Staff", "Staff"),
    ]

    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
        default="Student",
    )

    def __str__(self):
        if self.account_type == "School":
            return f"{self.user.username} - School Account"
        elif self.account_verification:
            return f"{self.user.username} - Verified"
        return f"{self.user.username} - Not Verified"


class UserBarcodeUsageHistory(models.Model):
    # foreign key to user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # barcode usage history
    barcode = models.ForeignKey('Barcode', on_delete=models.CASCADE)

    # timestamp of usage
    timestamp = models.BigIntegerField(default=None, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"


# user information
class UserProfile(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # student information
    name = models.CharField(max_length=100)
    information_id = models.CharField(max_length=100)

    # user profile image (base64 encoded png 128*128)
    user_profile_img = models.TextField()

    # account security fields
    failed_login_attempts = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - StudentID: **{self.information_id[-4:]}"


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

    # unique identifier for the barcode
    barcode_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, null=True
    )

    # barcode type (will be set up automatically)
    BARCODE_TYPE_CHOICES = [
        ("DynamicBarcode", "DynamicBarcode"),
        ("Others", "Others"),
    ]

    barcode_type = models.CharField(
        max_length=15,
        choices=BARCODE_TYPE_CHOICES,
        default="Others",
    )

    # barcode information
    barcode = models.TextField()
    linked_id = models.CharField(max_length=100, blank=True, null=True, default=None)

    # server verification information
    session = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.barcode_type == "DynamicBarcode":
            return f"Dynamic Barcode: barcode ending with {self.barcode[-4:]}"
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

    # timestamp verification
    timestamp_verification = models.BooleanField(default=True)

    # barcode pull settings
    barcode_pull = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Barcode Settings"
