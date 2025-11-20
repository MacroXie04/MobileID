"""
RSA Key Pair model for password encryption
"""

import uuid

from django.db import models
from django.utils import timezone


class RSAKeyPair(models.Model):
    """
    Stores RSA public/private key pairs for password encryption.
    Only one key pair should be active at a time.
    """

    # Key identifier (UUID)
    kid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique identifier for this key pair",
    )

    # Public key (PEM format) - safe to expose via API
    public_key = models.TextField(
        help_text=(
            "RSA public key in PEM format (BEGIN PUBLIC KEY...END PUBLIC KEY)"
        )
    )

    # Private key (PEM format) - NEVER exposed, encrypted at rest if possible
    private_key = models.TextField(
        help_text=(
            "RSA private key in PEM format (BEGIN PRIVATE KEY...END PRIVATE "
            "KEY)"
        )
    )

    # Key size (2048 or 4096)
    key_size = models.IntegerField(
        default=2048,
        choices=[(2048, "2048 bits"), (4096, "4096 bits")],
        help_text="RSA key size in bits",
    )

    # Active flag - only one should be active
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            "Whether this key pair is currently active for encryption/"
            "decryption"
        ),
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rotated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this key was rotated (deactivated)",
    )

    class Meta:
        app_label = "authn"
        db_table = "authn_rsa_keypair"
        verbose_name = "RSA Key Pair"
        verbose_name_plural = "RSA Key Pairs"
        ordering = ["-created_at"]

    def __str__(self):
        status = "ACTIVE" if self.is_active else "INACTIVE"
        return f"RSA-{self.key_size} ({self.kid.hex[:8]}...) - {status}"

    def deactivate(self):
        """Deactivate this key pair"""
        self.is_active = False
        self.rotated_at = timezone.now()
        self.save(update_fields=["is_active", "rotated_at"])
