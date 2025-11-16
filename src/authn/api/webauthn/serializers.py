import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from authn.models import FailedLoginAttempt, LoginAuditLog
from authn.utils.encryption import (
    decrypt_password,
    decrypt_password_with_nonce,
    is_encrypted_password,
    validate_encrypted_password_format,
)

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

        logger.warning("Login attempt blocked due to lock", extra={"username": attempt.username})
        self._log_auth_event(attempt.username, client_ip or attempt.ip_address, "blocked", reason="locked")
        raise serializers.ValidationError({"detail": self.generic_error_message})

    def _record_failed_attempt(self, attempt, client_ip):
        if not attempt:
            return

        attempt.attempt_count = min(
            self._max_failed_attempts(),
            attempt.attempt_count + 1,
        )
        if client_ip:
            attempt.ip_address = client_ip

        if attempt.attempt_count >= self._max_failed_attempts():
            attempt.locked_until = timezone.now() + self._lockout_duration()
            logger.warning("Account locked due to repeated failures", extra={"username": attempt.username})
            self._log_auth_event(attempt.username, client_ip or attempt.ip_address, "blocked", reason="locked")

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
            )
        except Exception:
            logger.exception("Failed to persist login audit log")

    def _get_user_agent(self):
        request = self.context.get("request") if hasattr(self, "context") else None
        if not request:
            return None
        return request.META.get("HTTP_USER_AGENT")


class EncryptedTokenObtainPairSerializer(_BaseLoginSerializer):
    """
    Custom serializer that supports decrypting RSA encrypted passwords
    """

    def validate(self, attrs):
        # Get password
        password = attrs.get("password")
        username = attrs.get(self.username_field) or attrs.get("username")
        client_ip = self._get_client_ip()

        logger.debug("Login payload received for username: %s", username)

        attempt_record = self._get_or_create_attempt(username, client_ip)
        self._enforce_account_lock(attempt_record, client_ip)

        # Check if password is encrypted
        is_encrypted = is_encrypted_password(password)
        logger.debug("Password identified as encrypted: %s", is_encrypted)

        if is_encrypted:
            try:
                # Decrypt password
                decrypted_password = decrypt_password(password)
                # Replace with decrypted password
                attrs["password"] = decrypted_password
            except ValueError as exc:
                # Decryption failed, log detailed error information
                logger.error("Password decryption failed: %s", str(exc))
                self._log_auth_event(username, client_ip, "failure", reason="decrypt_failed")

                raise serializers.ValidationError({"detail": self.generic_error_message})

        # Call parent class validation method
        try:
            data = super().validate(attrs)
        except AuthenticationFailed as exc:
            self._record_failed_attempt(attempt_record, client_ip)
            self._log_auth_event(username, client_ip, "failure", reason="invalid_credentials")
            raise AuthenticationFailed(detail=self.generic_error_message) from exc
        except TokenError as exc:  # pragma: no cover - TokenError should be rare
            self._record_failed_attempt(attempt_record, client_ip)
            self._log_auth_event(username, client_ip, "failure", reason="token_error")
            raise AuthenticationFailed(detail=self.generic_error_message) from exc

        self._reset_failed_attempts(attempt_record, client_ip)
        self._log_auth_event(username, client_ip, "success")
        return data


class RSAEncryptedLoginSerializer(_BaseLoginSerializer):
    """
    Serializer that ENFORCES RSA-encrypted password submissions with nonce.
    Rejects unencrypted passwords for enhanced security.
    """

    def validate(self, attrs):
        # Get password
        password = attrs.get("password")
        username = attrs.get(self.username_field) or attrs.get("username")
        client_ip = self._get_client_ip()

        logger.debug("RSA encrypted login attempt for username: %s", username)

        attempt_record = self._get_or_create_attempt(username, client_ip)
        self._enforce_account_lock(attempt_record, client_ip)

        # ENFORCE encrypted password - reject unencrypted
        if not password:
            logger.warning("Login attempt with missing password")
            self._log_auth_event(username, client_ip, "failure", reason="missing_password")
            raise serializers.ValidationError({"detail": self.generic_error_message})

        # Validate encrypted password format
        try:
            validate_encrypted_password_format(password)
        except ValueError as exc:
            logger.warning("Login attempt with invalid encrypted password format: %s", str(exc))
            self._log_auth_event(username, client_ip, "failure", reason="invalid_encryption_format")
            raise serializers.ValidationError({"detail": self.generic_error_message})

        # Decrypt password with nonce validation
        try:
            decrypted_password, nonce = decrypt_password_with_nonce(password)
            logger.debug("Password decrypted successfully, nonce length: %d", len(nonce))
            # Replace with decrypted password
            attrs["password"] = decrypted_password
        except ValueError as exc:
            # Decryption failed
            logger.error("Password decryption failed: %s", str(exc))
            self._log_auth_event(username, client_ip, "failure", reason="decrypt_failed")
            raise serializers.ValidationError({"detail": self.generic_error_message})

        # Call parent class validation method
        try:
            data = super().validate(attrs)
        except AuthenticationFailed as exc:
            self._record_failed_attempt(attempt_record, client_ip)
            self._log_auth_event(username, client_ip, "failure", reason="invalid_credentials")
            raise AuthenticationFailed(detail=self.generic_error_message) from exc
        except TokenError as exc:  # pragma: no cover - TokenError should be rare
            self._record_failed_attempt(attempt_record, client_ip)
            self._log_auth_event(username, client_ip, "failure", reason="token_error")
            raise AuthenticationFailed(detail=self.generic_error_message) from exc

        self._reset_failed_attempts(attempt_record, client_ip)
        self._log_auth_event(username, client_ip, "success")
        return data

