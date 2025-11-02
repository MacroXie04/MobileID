"""
Password encryption and decryption utilities
"""
import base64
import logging
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)

# RSA private key - used for password decryption
RSA_PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCzX7DyVkegAYQm
MbrdlW4l2FXxn73a3kZjaGXCG3OQBzBn6w9HhhSZFKpacDb0HrPm1VOtB8S0eGoD
x8rCYC/TZERZV7wtdQztUeMq+TJarPCIrLiDWRS97CQxGPUaU62boVdb+TuKsxl0
HixMJLbtjbmUT2bkqufnkQA9T6ChgOZlhPArGB6bPmgRqAZwMgtDKWBE08Rtaano
e9qcuyiDOiv7FWgBnb/+R7vabJVLxZgJ4/GOszLV7Oh+5Rag94zKFIgVG8xCYwpY
i5WH2Hb8Oul8ylW2FFoBRbhDbfwXhCVwjP6kqP1Hyvy4WOACjPJJb3S/EUmnU7wB
ajQBGyUvAgMBAAECggEASgogJE+X3gRyMz/ItckF/8oV45f/ynWAUW0Yv7AMGfHV
ubdNhcTjALMGhDEYhdicgpYgpWX0/FdNz0SrPWNtqlCTY9tymcLcdKMd5TGaZtJG
sOu2d8UP6jssTzXRii3rFbfZsuWj/aLiyUrhFwb6mQCsjvrdalrfQXbZRfV1xOOZ
ZAwbbLBWX9+29dMS+WO36HyX/V7QDXs7T/J0VdWMTOhxmETGyw3l0gBliwDfSKzr
L8av39bkNq3tVPstTdJqpiYikWrnK/z0ecakkOywTrV7xthNwVvikg0k5VKWvdAu
ULouhI0Rgi442zPBMUQtgnn0mpPuoJxx+s4qzC3KzQKBgQDwWUmhsVpl1pfq1q0s
j/gve220PQiPTFQ4ec+m5IffQqPR0qmYNjOwLbkUgq8De5p0L0H6zH91Eic6Z7fw
Quc6EEKEqgMzT3nNvhfF9APdonzfxEu/T9Y4OfER/J/XrKpbU4EieB9f9/SDtVLP
aG6A1vpM+b2zspEVTnUoreizkwKBgQC/Dez2u4h62gcDVOGHYi0Ppu2XgS2oBZ94
HJ9IIlfhRL6CneWLQKeqSFCdoST4ExUf643yg5W1/9Nm43fVI1m9n8ilsSirlVmE
FUqUhmd4IoepRpeEmN2yDdEmolcmAhdfHuuMsXImPGNkbfgIFbGRiUAqA2k3nCm8
Ry1CwiyBdQKBgQCrH5dKNWDcYyZ0wHY55SNagzG/gzkF9d18/FV5SProXaUPrkKr
qeOxS0ycKtN60lVM5Zy/eTxCWTNu5QvUV34UHCGQHQ/8R1i8wNxiR3M9KQRpuXQI
+UnXbIGUQd54i2obbd/ib84+4ObJo58bJwqOVwGNLr7/I2Mi3WKTHQcyWwKBgAbu
sGx7fYZHpv199Pj+nPf2bKSUsV1pZtHq5/SsGlg4MFl49T1KSUsqeJJfqIG/34Ja
/7mPAL2r3LXdBxoawETbKWKpvPoM30SlqSEeh16akiWYRCMxkMnHKpGmTlc4uDRh
YNaoEaZFhq28N8XDU8AeJM/hc83qwrDsPD4x4X+JAoGBAMNdMdwp0w/sBUFe9PUl
RFou02TWMA3hvRMgMe8JHpFbO9Z2LMZV957EIiNnd6eejPONRSuQaVRdZ+dgKebL
nurMFGXsCkJ5OSW9gXb2ZS+rqHfpYzFivQP3Qmu4qog2TJkSFFsdh5ffTHHL5UL4
WjxMUoe9Vh6DGMJF3bwHVUQr
-----END PRIVATE KEY-----"""


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
        # Load private key
        private_key = serialization.load_pem_private_key(
            RSA_PRIVATE_KEY_PEM.encode(),
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
