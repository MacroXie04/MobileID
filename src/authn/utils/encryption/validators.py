import base64


def is_encrypted_password(password):
    """
    Check if password is encrypted (basic RSA Base64 heuristic).
    """

    if not password or len(password) < 100:
        return False

    try:
        decoded = base64.b64decode(password)
        return 200 <= len(decoded) <= 600
    except Exception:
        return False


def validate_encrypted_password_format(encrypted_password):
    """
    Validate that the encrypted password is in the correct RSA format.
    """

    if not encrypted_password:
        raise ValueError("Encrypted password cannot be empty")

    if not isinstance(encrypted_password, str):
        raise ValueError("Encrypted password must be a string")

    if len(encrypted_password) < 100:
        raise ValueError(
            "Encrypted password is too short to be valid RSA ciphertext"
        )

    try:
        decoded = base64.b64decode(encrypted_password)
    except Exception as exc:
        raise ValueError(f"Invalid Base64 encoding: {str(exc)}")

    if len(decoded) < 200 or len(decoded) > 600:
        raise ValueError(
            f"Invalid RSA ciphertext length: {len(decoded)} bytes"
        )

    return True
