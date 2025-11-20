from django.conf import settings
from django.db import models
from django.utils import timezone


class AdminOneTimePass(models.Model):
    """
    Model to store one-time passwords for admin authentication.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_otps",
    )
    pass_code = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        app_label = "core"
        verbose_name = "Admin One-Time Password"
        verbose_name_plural = "Admin One-Time Passwords"
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.user} (Expires: {self.expires_at})"

    def is_valid(self):
        """
        Check if the OTP is valid (not used and not expired).
        """
        return not self.is_used and timezone.now() < self.expires_at
