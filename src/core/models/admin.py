"""
Admin models for tracking admin access and actions.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class AdminAuditLog(models.Model):
    """
    Audit log for admin access and actions.

    Tracks all admin page access, login attempts, and sensitive operations.
    """

    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    ADD = "add"
    CHANGE = "change"
    DELETE = "delete"
    ACTION = "action"

    ACTION_CHOICES = [
        (LOGIN, "Login"),
        (LOGOUT, "Logout"),
        (VIEW, "View"),
        (ADD, "Add"),
        (CHANGE, "Change"),
        (DELETE, "Delete"),
        (ACTION, "Action"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="admin_audit_logs",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    resource = models.CharField(
        max_length=200,
        blank=True,
        help_text="Model or resource being accessed",
    )
    success = models.BooleanField(default=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional details about the action",
    )

    class Meta:
        app_label = "core"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["action"]),
            models.Index(fields=["success"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["ip_address"]),
        ]
        verbose_name = "Admin Audit Log"
        verbose_name_plural = "Admin Audit Logs"

    def __str__(self):
        try:
            username = self.user.username if self.user else "anonymous"
        except AttributeError:
            username = str(self.user) if self.user else "anonymous"
        return (
            f"{username} - {self.action} - {self.resource or 'N/A'} at "
            f"{self.timestamp.isoformat()}"
        )


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
