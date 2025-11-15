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

    username = models.CharField(max_length=150, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    reason = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Login Audit Log"
        verbose_name_plural = "Login Audit Logs"

    def __str__(self):
        return f"{self.username or 'anonymous'} - {self.result} at {self.created_at.isoformat()}"

