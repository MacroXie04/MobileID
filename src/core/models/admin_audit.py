"""
Admin audit log model for tracking admin access and actions.
"""

from django.conf import settings
from django.db import models


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
    action = models.CharField(
        max_length=20, choices=ACTION_CHOICES, db_index=True
    )
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
