import logging
from datetime import timedelta

from authn.repositories import SecurityRepository
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
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

    def _enforce_account_lock(self, username, client_ip):
        if not username:
            return

        if SecurityRepository.is_account_locked(username):
            logger.warning(
                "Login attempt blocked due to lock",
                extra={"username": username},
            )
            self._log_auth_event(
                username,
                client_ip,
                "blocked",
                reason="locked",
            )
            raise serializers.ValidationError({"detail": self.generic_error_message})

    def _record_failed_attempt(self, username, client_ip):
        if not username:
            return

        SecurityRepository.increment_failed_attempt(
            username=username,
            ip_address=client_ip,
            max_attempts=self._max_failed_attempts(),
            lockout_duration=self._lockout_duration(),
        )

    def _reset_failed_attempts(self, username, client_ip):
        if not username:
            return
        SecurityRepository.reset_failed_attempts(username, client_ip)

    def _max_failed_attempts(self):
        return getattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 5)

    def _lockout_duration(self):
        minutes = getattr(settings, "ACCOUNT_LOCKOUT_DURATION", 30)
        return timedelta(minutes=minutes)

    def _log_auth_event(self, username, client_ip, result, reason=None):
        user_agent = self._get_user_agent()
        success_flag = result == "success"
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
            SecurityRepository.create_audit_log(
                username=username or "",
                user_id=related_user.id if related_user else None,
                ip_address=client_ip,
                user_agent=user_agent or "",
                result=result,
                reason=reason or "",
                success=success_flag,
            )
        except Exception:
            logger.exception("Failed to persist login audit log")

    def _get_user_agent(self):
        request = self.context.get("request") if hasattr(self, "context") else None
        if not request:
            return None
        return request.META.get("HTTP_USER_AGENT")


class PlaintextLoginSerializer(_BaseLoginSerializer):
    """
    Login serializer that accepts plaintext username/password credentials.
    """

    def validate(self, attrs):
        password = attrs.get("password")
        username = attrs.get(self.username_field) or attrs.get("username")
        client_ip = self._get_client_ip()

        logger.debug("Login attempt for username: %s", username)

        self._enforce_account_lock(username, client_ip)

        if not password:
            logger.warning("Login attempt with missing password")
            self._log_auth_event(
                username, client_ip, "failure", reason="missing_password"
            )
            raise serializers.ValidationError({"detail": self.generic_error_message})

        try:
            data = super().validate(attrs)
        except AuthenticationFailed as exc:
            self._record_failed_attempt(username, client_ip)
            self._log_auth_event(
                username, client_ip, "failure", reason="invalid_credentials"
            )
            raise AuthenticationFailed(detail=self.generic_error_message) from exc
        except TokenError as exc:
            self._record_failed_attempt(username, client_ip)
            self._log_auth_event(username, client_ip, "failure", reason="token_error")
            raise AuthenticationFailed(detail=self.generic_error_message) from exc

        self._reset_failed_attempts(username, client_ip)
        self._log_auth_event(username, client_ip, "success")
        return data
