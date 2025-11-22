import logging
from datetime import timedelta

from authn.models import FailedLoginAttempt, LoginAuditLog
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

logger = logging.getLogger(__name__)


class _BaseLoginSerializer(TokenObtainPairSerializer):
    generic_error_message = "Invalid username or password."

    def _get_client_ip(self):
        request = self.context.get("request") if hasattr(self, "context") else None
        if not request:
            return None
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def _get_or_create_attempt(self, username, client_ip):
        if not username:
            return None
        attempt, _ = FailedLoginAttempt.objects.get_or_create(
            username=username,
            defaults={"ip_address": client_ip},
        )
        return attempt

    def _enforce_account_lock(self, attempt, client_ip):
        if not attempt or not attempt.locked_until:
            return

        if attempt.locked_until <= timezone.now():
            attempt.locked_until = None
            attempt.attempt_count = 0
            attempt.save()
            return

        logger.warning(
            "Login attempt blocked due to lock",
            extra={"username": attempt.username},
        )
        self._log_auth_event(
            attempt.username,
            client_ip or attempt.ip_address,
            "blocked",
            reason="locked",
        )
        raise serializers.ValidationError({"detail": self.generic_error_message})

    def _record_failed_attempt(self, attempt, client_ip):
        if not attempt:
            return

        attempt.attempt_count = min(
            self._max_failed_attempts(), attempt.attempt_count + 1
        )
        if client_ip:
            attempt.ip_address = client_ip

        if attempt.attempt_count >= self._max_failed_attempts():
            attempt.locked_until = timezone.now() + self._lockout_duration()
            logger.warning(
                "Account locked due to repeated failures",
                extra={"username": attempt.username},
            )
            self._log_auth_event(
                username=attempt.username,
                client_ip=client_ip or attempt.ip_address,
                result="blocked",
                reason="locked",
            )

        attempt.save()

    def _reset_failed_attempts(self, attempt, client_ip):
        if not attempt:
            return

        updated = False
        if attempt.attempt_count or attempt.locked_until:
            attempt.attempt_count = 0
            attempt.locked_until = None
            updated = True

        if client_ip and attempt.ip_address != client_ip:
            attempt.ip_address = client_ip
            updated = True

        if updated:
            attempt.save()

    def _max_failed_attempts(self):
        return getattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 5)

    def _lockout_duration(self):
        minutes = getattr(settings, "ACCOUNT_LOCKOUT_DURATION", 30)
        return timedelta(minutes=minutes)

    def _log_auth_event(self, username, client_ip, result, reason=None):
        user_agent = self._get_user_agent()
        success_flag = result == LoginAuditLog.SUCCESS
        related_user = getattr(self, "user", None) if success_flag else None
        logger.info(
            "Login attempt",
            extra={
                "username": username,
                "ip": client_ip,
                "result": result,
                "reason": reason,
            },
        )
        try:
            LoginAuditLog.objects.create(
                username=username or "",
                ip_address=client_ip,
                user_agent=user_agent or "",
                result=result,
                reason=reason or "",
                success=success_flag,
                user=related_user,
            )
        except Exception:
            logger.exception("Failed to persist login audit log")

    def _get_user_agent(self):
        request = self.context.get("request") if hasattr(self, "context") else None
        if not request:
            return None
        return request.META.get("HTTP_USER_AGENT")
