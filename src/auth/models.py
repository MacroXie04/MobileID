from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
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
    profile_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

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

    def __str__(self):
        return f"{self.name} - ID: **{self.information_id[-4:]}"


class Passkey(models.Model):
    # foreign key to user (allow multiple passkeys per user)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="passkeys")

    # passkey credential id
    credential_id = models.CharField(max_length=191, unique=True)

    # passkey public key
    public_key = models.TextField()

    # passkey sign count
    sign_count = models.IntegerField(default=0)

    # passkey transports
    transports = models.JSONField(null=True, blank=True)

    # passkey created at
    created_at = models.DateTimeField(auto_now_add=True)
