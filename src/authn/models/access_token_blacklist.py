"""
Access Token Blacklist model for immediate session revocation.

When a device is logged out, both the refresh token AND access token
need to be invalidated. Since access tokens are stateless JWTs,
we need to track revoked access token JTIs to reject them before expiry.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class AccessTokenBlacklist(models.Model):
    """
    Tracks blacklisted access token JTIs.

    When a device/session is revoked:
    1. The refresh token is blacklisted via simplejwt's BlacklistedToken
    2. The access token JTI is added here for immediate rejection

    Entries should be cleaned up periodically (after access token lifetime expires).
    """

    jti = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blacklisted_access_tokens",
    )
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    # Store expiry for cleanup purposes
    expires_at = models.DateTimeField()

    class Meta:
        app_label = "authn"
        verbose_name = "Blacklisted Access Token"
        verbose_name_plural = "Blacklisted Access Tokens"
        indexes = [
            models.Index(fields=["jti"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Blacklisted: {self.jti[:20]}... (user: {self.user_id})"

    @classmethod
    def is_blacklisted(cls, jti):
        """
        Check if an access token JTI is blacklisted.
        Uses exists() for efficient lookup.
        """
        return cls.objects.filter(jti=jti).exists()

    @classmethod
    def blacklist_token(cls, jti, user, expires_at):
        """
        Add an access token JTI to the blacklist.
        """
        cls.objects.get_or_create(
            jti=jti,
            defaults={
                "user": user,
                "expires_at": expires_at,
            },
        )

    @classmethod
    def cleanup_expired(cls):
        """
        Remove expired entries from the blacklist.
        Should be run periodically via management command or celery task.
        """
        return cls.objects.filter(expires_at__lt=timezone.now()).delete()
