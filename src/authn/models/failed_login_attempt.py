from django.db import models


class FailedLoginAttempt(models.Model):
    username = models.CharField(max_length=150, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "authn"
        ordering = ["-last_attempt"]
        verbose_name = "Failed Login Attempt"
        verbose_name_plural = "Failed Login Attempts"

    def __str__(self):
        status = "locked" if self.is_locked else "active"
        return f"{self.username} ({status})"

    @property
    def is_locked(self):
        from django.utils import timezone

        return bool(self.locked_until and self.locked_until > timezone.now())
