import uuid

from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator
from django.db import models


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


class PasskeyCredential(models.Model):
    """
    WebAuthn/FIDO2 passkey bound to a single user.
    A user can have at most one passkey in this app.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="passkey")
    # Base64URL-encoded credential ID
    credential_id = models.CharField(max_length=255, unique=True)
    # Authenticator public key (base64url of COSE key bytes)
    public_key = models.TextField()
    # Sign counter for cloning detection
    sign_count = models.BigIntegerField(default=0)
    # Attestation format for reference/debugging
    attestation_format = models.CharField(max_length=100, blank=True, default="")
    # When created/updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Passkey for {self.user.username} ({self.credential_id[:8]}...)"
