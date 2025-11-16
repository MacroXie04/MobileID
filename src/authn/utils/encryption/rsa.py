import base64
import logging
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from authn.utils.keys import get_active_rsa_keypair

logger = logging.getLogger(__name__)


def get_rsa_private_key():
    """
    Get RSA private key from environment variable (legacy support).
    """

    rsa_private_key = os.getenv("RSA_PRIVATE_KEY")
    if not rsa_private_key:
        logger.error("RSA_PRIVATE_KEY environment variable is not set")
        raise ValueError("RSA_PRIVATE_KEY environment variable is required for password decryption")
    return rsa_private_key


def decrypt_rsa_ciphertext(encrypted_data_b64, private_key_pem=None):
    """
    Decrypt RSA ciphertext using private key with OAEP preference.
    """

    try:
        if private_key_pem is None:
            key_pair = get_active_rsa_keypair()
            private_key_pem = key_pair.private_key

        private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
        encrypted_data = base64.b64decode(encrypted_data_b64)

        try:
            return private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except ValueError:
            decrypted_data = private_key.decrypt(
                encrypted_data,
                padding.PKCS1v15(),
            )
            return decrypted_data

    except Exception as exc:
        logger.error("RSA decryption failed: %s", str(exc))
        raise ValueError("RSA decryption failed")

