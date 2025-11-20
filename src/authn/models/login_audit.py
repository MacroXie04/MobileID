from django.conf import settings
from django.db import models


class LoginAuditLog(models.Model):
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"

    RESULT_CHOICES = [
        (SUCCESS, "Success"),
        (FAILURE, "Failure"),
        (BLOCKED, "Blocked"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_audit_logs",
    )
    username = models.CharField(max_length=150, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    reason = models.CharField(max_length=64, blank=True)
    success = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "authn"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["success"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Login Audit Log"
        verbose_name_plural = "Login Audit Logs"

    def __str__(self):
        status = "success" if self.success else self.result
        return (
            f"{self.username or 'anonymous'} - {status} at "
            f"{self.created_at.isoformat()}"
        )
