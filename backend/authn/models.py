from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime
import uuid

# user information
class UserProfile(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # information
    name = models.CharField(max_length=100)
    information_id = models.CharField(max_length=100)

    # user uuid
    profile_uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, null=True
    )

    # user profile image (base64 encoded png 128*128)
    user_profile_img = models.TextField()

    def __str__(self):
        return f"{self.name} - ID: **{self.information_id[-4:]}"


# user account type
class UserAccount(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # user account type settings
    ACCOUNT_TYPE_CHOICES = [
        ("School", "School"),
        ("User", "User"),
        ("Staff", "Staff"),
    ]

    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
        default="User",
    )

    def __str__(self):
        return f"{self.user.username} - {self.account_type} Account"


class UserExtendedData(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # extended data stored as JSON
    extended_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username} - Extended Data"

class QuickAction(models.Model):
    # action name
    action_name = models.CharField(max_length=100, unique=True)

    # action description
    action_description = models.TextField(max_length=255, blank=True)

    # patch to apply
    json_patch = models.JSONField(help_text="JSON Patch to apply to the user extended data")

    def __str__(self):
        return self.action_name

class UserChangeLog(models.Model):
    # foreign key to staff user and target user
    staff_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_user')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='target_user')

    # timestamp of change
    timestamp = models.DateTimeField(auto_now_add=True)

    # description of the change
    change_description = models.TextField(max_length=255, blank=True)

    # data before and after the change
    data_before = models.JSONField(default=dict, blank=True)
    data_after = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Change by {self.staff_user.username} on {self.target_user.username} at {self.timestamp}"






