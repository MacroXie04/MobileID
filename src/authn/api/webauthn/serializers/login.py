import logging

from authn.services.login_challenge import consume_login_challenge
from authn.utils.encryption import (
    decrypt_password,
    decrypt_password_with_nonce,
    is_encrypted_password,
    validate_encrypted_password_format,
)
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError

from .base import _BaseLoginSerializer

logger = logging.getLogger(__name__)


class EncryptedTokenObtainPairSerializer(_BaseLoginSerializer):
    """
    Custom serializer that supports decrypting RSA encrypted passwords
    """

    def validate(self, attrs):
        password = attrs.get("password")
        username = attrs.get(self.username_field) or attrs.get("username")
        client_ip = self._get_client_ip()

        logger.debug("Login payload received for username: %s", username)

        attempt_record = self._get_or_create_attempt(username, client_ip)
        self._enforce_account_lock(attempt_record, client_ip)

        is_encrypted = is_encrypted_password(password)
        logger.debug("Password identified as encrypted: %s", is_encrypted)

        if is_encrypted:
            try:
                decrypted_password = decrypt_password(password)
                attrs["password"] = decrypted_password
            except ValueError as exc:
                logger.error("Password decryption failed: %s", str(exc))
                self._log_auth_event(
                    username, client_ip, "failure", reason="decrypt_failed"
                )
                raise serializers.ValidationError(
                    {"detail": self.generic_error_message}
                )

        try:
            data = super().validate(attrs)
        except AuthenticationFailed as exc:
            self._record_failed_attempt(attempt_record, client_ip)
            self._log_auth_event(
                username, client_ip, "failure", reason="invalid_credentials"
            )
            raise AuthenticationFailed(
                detail=self.generic_error_message
            ) from exc
        except TokenError as exc:  # pragma: no cover
            self._record_failed_attempt(attempt_record, client_ip)
            self._log_auth_event(
                username, client_ip, "failure", reason="token_error"
            )
            raise AuthenticationFailed(
                detail=self.generic_error_message
            ) from exc

        self._reset_failed_attempts(attempt_record, client_ip)
        self._log_auth_event(username, client_ip, "success")
        return data


class RSAEncryptedLoginSerializer(_BaseLoginSerializer):
    """
    Serializer that ENFORCES RSA-encrypted password submissions with nonce.
    Rejects unencrypted passwords for enhanced security.
    """

    def validate(self, attrs):
        password = attrs.get("password")
        username = attrs.get(self.username_field) or attrs.get("username")
        client_ip = self._get_client_ip()

        logger.debug("RSA encrypted login attempt for username: %s", username)

        attempt_record = self._get_or_create_attempt(username, client_ip)
        self._enforce_account_lock(attempt_record, client_ip)

        if not password:
            logger.warning("Login attempt with missing password")
            self._log_auth_event(
                username, client_ip, "failure", reason="missing_password"
            )
            raise serializers.ValidationError(
                {"detail": self.generic_error_message}
            )

        try:
            validate_encrypted_password_format(password)
        except ValueError as exc:
            logger.warning(
                "Login attempt with invalid encrypted password format: %s",
                str(exc),
            )
            self._log_auth_event(
                username,
                client_ip,
                "failure",
                reason="invalid_encryption_format",
            )
            raise serializers.ValidationError(
                {"detail": self.generic_error_message}
            )

        try:
            decrypted_password, nonce = decrypt_password_with_nonce(password)
            logger.debug(
                "Password decrypted successfully, nonce length: %d", len(nonce)
            )
            attrs["password"] = decrypted_password
        except ValueError as exc:
            logger.error("Password decryption failed: %s", str(exc))
            self._log_auth_event(
                username, client_ip, "failure", reason="decrypt_failed"
            )
            raise serializers.ValidationError(
                {"detail": self.generic_error_message}
            )

        try:
            consume_login_challenge(nonce)
        except ValueError:
            logger.warning(
                "Login attempt with invalid or expired nonce for %s", username
            )
            self._log_auth_event(
                username, client_ip, "failure", reason="invalid_nonce"
            )
            raise serializers.ValidationError(
                {"detail": self.generic_error_message}
            )

        try:
            data = super().validate(attrs)
        except AuthenticationFailed as exc:
            self._record_failed_attempt(attempt_record, client_ip)
            self._log_auth_event(
                username, client_ip, "failure", reason="invalid_credentials"
            )
            raise AuthenticationFailed(
                detail=self.generic_error_message
            ) from exc
        except TokenError as exc:  # pragma: no cover
            self._record_failed_attempt(attempt_record, client_ip)
            self._log_auth_event(
                username, client_ip, "failure", reason="token_error"
            )
            raise AuthenticationFailed(
                detail=self.generic_error_message
            ) from exc

        self._reset_failed_attempts(attempt_record, client_ip)
        self._log_auth_event(username, client_ip, "success")
        return data
