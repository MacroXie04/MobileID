import json
import logging

from .rsa import decrypt_rsa_ciphertext

logger = logging.getLogger(__name__)


def decrypt_password_with_nonce(encrypted_password_b64):
    """
    Decrypt password that was encrypted with a nonce.
    """

    try:
        decrypted_bytes = decrypt_rsa_ciphertext(encrypted_password_b64)

        try:
            payload = json.loads(decrypted_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error(
                "Failed to parse decrypted payload as JSON: %s", str(exc)
            )
            raise ValueError("Invalid encrypted payload format")

        if not isinstance(payload, dict):
            raise ValueError("Decrypted payload must be a JSON object")

        if "password" not in payload:
            raise ValueError("Decrypted payload must contain 'password' field")

        if "nonce" not in payload:
            raise ValueError("Decrypted payload must contain 'nonce' field")

        password = payload["password"]
        nonce = payload["nonce"]

        if not isinstance(nonce, str) or len(nonce) < 16:
            raise ValueError("Invalid nonce format or length")

        if not isinstance(password, str) or len(password) == 0:
            raise ValueError("Password cannot be empty")

        return password, nonce

    except ValueError:
        raise
    except Exception as exc:
        logger.error("Password decryption with nonce failed: %s", str(exc))
        raise ValueError("Password decryption failed")


def decrypt_password(encrypted_password):
    """
    Decrypt password using RSA private key (legacy support, tries nonce format
    first).
    """

    try:
        password, _ = decrypt_password_with_nonce(encrypted_password)
        return password
    except ValueError:
        try:
            decrypted_bytes = decrypt_rsa_ciphertext(encrypted_password)
            return decrypted_bytes.decode("utf-8")
        except Exception as exc:
            logger.error(
                "Password decryption failed in legacy path: %s", str(exc)
            )
            raise ValueError("Password decryption failed")
    except Exception as exc:
        logger.error("Password decryption failed: %s", str(exc))
        raise ValueError("Password decryption failed")
