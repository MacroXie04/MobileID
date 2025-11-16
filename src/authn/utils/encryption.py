"""
Password encryption and decryption utilities
"""
import base64
import json
import logging
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from authn.utils.keys import get_active_rsa_keypair

logger = logging.getLogger(__name__)


def get_rsa_private_key():
    """
    Get RSA private key from environment variable (legacy support).
    
    Returns:
        str: RSA private key in PEM format
        
    Raises:
        ValueError: If RSA_PRIVATE_KEY is not set in environment
    """
    rsa_private_key = os.getenv("RSA_PRIVATE_KEY")
    if not rsa_private_key:
        logger.error("RSA_PRIVATE_KEY environment variable is not set")
        raise ValueError(
            "RSA_PRIVATE_KEY environment variable is required for password decryption"
        )
    return rsa_private_key


def decrypt_rsa_ciphertext(encrypted_data_b64, private_key_pem=None):
    """
    Decrypt RSA ciphertext using private key.
    
    Args:
        encrypted_data_b64 (str): Base64-encoded encrypted data
        private_key_pem (str, optional): Private key in PEM format. If None, uses active key from DB.
        
    Returns:
        bytes: Decrypted plaintext bytes
        
    Raises:
        ValueError: If decryption fails
    """
    try:
        # Get private key
        if private_key_pem is None:
            key_pair = get_active_rsa_keypair()
            private_key_pem = key_pair.private_key
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None
        )

        # Decode Base64
        encrypted_data = base64.b64decode(encrypted_data_b64)

        # Decrypt - JSEncrypt uses PKCS1 padding
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.PKCS1v15()
        )

        return decrypted_data

    except Exception as e:
        logger.error(f"RSA decryption failed: {str(e)}")
        raise ValueError("RSA decryption failed")


def decrypt_password_with_nonce(encrypted_password_b64):
    """
    Decrypt password that was encrypted with a nonce.
    
    Expected format: JSON string containing {"nonce": "...", "password": "..."}
    The entire JSON string is encrypted, then Base64 encoded.
    
    Args:
        encrypted_password_b64 (str): Base64-encoded encrypted JSON payload
        
    Returns:
        tuple: (password: str, nonce: str)
        
    Raises:
        ValueError: If decryption or parsing fails
    """
    try:
        # Decrypt the ciphertext
        decrypted_bytes = decrypt_rsa_ciphertext(encrypted_password_b64)
        
        # Parse JSON payload
        try:
            payload = json.loads(decrypted_bytes.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse decrypted payload as JSON: {str(e)}")
            raise ValueError("Invalid encrypted payload format")
        
        # Validate payload structure
        if not isinstance(payload, dict):
            raise ValueError("Decrypted payload must be a JSON object")
        
        if "password" not in payload:
            raise ValueError("Decrypted payload must contain 'password' field")
        
        if "nonce" not in payload:
            raise ValueError("Decrypted payload must contain 'nonce' field")
        
        password = payload["password"]
        nonce = payload["nonce"]
        
        # Validate nonce (should be hex string, typically 16-32 bytes = 32-64 hex chars)
        if not isinstance(nonce, str) or len(nonce) < 16:
            raise ValueError("Invalid nonce format or length")
        
        # Validate password
        if not isinstance(password, str) or len(password) == 0:
            raise ValueError("Password cannot be empty")
        
        return password, nonce
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Password decryption with nonce failed: {str(e)}")
        raise ValueError("Password decryption failed")


def decrypt_password(encrypted_password):
    """
    Decrypt password using RSA private key (legacy support, tries nonce format first).
    
    Args:
        encrypted_password (str): Encrypted password (Base64 encoded)
        
    Returns:
        str: Decrypted plaintext password
        
    Raises:
        ValueError: Raised when decryption fails
    """
    try:
        # Try new format first (with nonce)
        password, _ = decrypt_password_with_nonce(encrypted_password)
        return password
    except ValueError:
        # Fall back to legacy format (direct password encryption)
        try:
            decrypted_bytes = decrypt_rsa_ciphertext(encrypted_password)
            return decrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Password decryption failed: {str(e)}")
        raise ValueError("Password decryption failed")


def is_encrypted_password(password):
    """
    Check if password is encrypted (check if it's RSA encrypted Base64 format)
    
    Args:
        password (str): Password string
        
    Returns:
        bool: Whether the password is encrypted
    """
    if not password or len(password) < 100:
        return False

    try:
        # Try Base64 decoding
        decoded = base64.b64decode(password)
        # JSEncrypt uses PKCS1 padding, encrypted length is usually 256 bytes for 2048-bit keys
        # For 4096-bit keys, it's 512 bytes
        # But considering different padding methods, we check a reasonable range
        return len(decoded) >= 200 and len(decoded) <= 600
    except:
        return False


def validate_encrypted_password_format(encrypted_password):
    """
    Validate that the encrypted password is in the correct RSA format.
    
    Args:
        encrypted_password (str): Encrypted password string
        
    Returns:
        bool: True if format is valid
        
    Raises:
        ValueError: If format is invalid
    """
    if not encrypted_password:
        raise ValueError("Encrypted password cannot be empty")
    
    if not isinstance(encrypted_password, str):
        raise ValueError("Encrypted password must be a string")
    
    # Check minimum length (Base64 encoded RSA ciphertext should be at least 100 chars)
    if len(encrypted_password) < 100:
        raise ValueError("Encrypted password is too short to be valid RSA ciphertext")
    
    # Try Base64 decoding
    try:
        decoded = base64.b64decode(encrypted_password)
    except Exception as e:
        raise ValueError(f"Invalid Base64 encoding: {str(e)}")
    
    # Check decoded length (RSA-2048: 256 bytes, RSA-4096: 512 bytes)
    if len(decoded) < 200 or len(decoded) > 600:
        raise ValueError(f"Invalid RSA ciphertext length: {len(decoded)} bytes")
    
    return True
