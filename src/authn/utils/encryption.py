"""
Password encryption and decryption utilities
"""
import base64
import logging
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)


def get_rsa_private_key():
    """
    Get RSA private key from environment variable.
    
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


def decrypt_password(encrypted_password):
    """
    Decrypt password using RSA private key
    
    Args:
        encrypted_password (str): Encrypted password (Base64 encoded)
        
    Returns:
        str: Decrypted plaintext password
        
    Raises:
        ValueError: Raised when decryption fails
    """
    try:
        # Get private key from environment
        rsa_private_key_pem = get_rsa_private_key()
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            rsa_private_key_pem.encode(),
            password=None
        )

        # Decode Base64
        encrypted_data = base64.b64decode(encrypted_password)

        # Decrypt - JSEncrypt uses PKCS1 padding
        decrypted_password = private_key.decrypt(
            encrypted_data,
            padding.PKCS1v15()
        )

        return decrypted_password.decode('utf-8')

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
        # JSEncrypt uses PKCS1 padding, encrypted length is usually 256 bytes
        # But considering different padding methods, we check a reasonable range
        return len(decoded) >= 200 and len(decoded) <= 300
    except:
        return False
