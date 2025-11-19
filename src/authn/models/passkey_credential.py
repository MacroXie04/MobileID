from django.contrib.auth.models import User
from django.db import models


class PasskeyCredential(models.Model):
    """
    WebAuthn/FIDO2 passkey bound to a single user.
    A user can have at most one passkey in this app.
    """

    # foreign key to user
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

    class Meta:
        app_label = "authn"

    def __str__(self):
        return f"Passkey for {self.user.username} ({self.credential_id[:8]}...)"
