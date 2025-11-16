# Import all models to maintain backward compatibility
from .user_profile import UserProfile
from .passkey_credential import PasskeyCredential
from .failed_login_attempt import FailedLoginAttempt
from .login_audit import LoginAuditLog
from .rsa_keys import RSAKeyPair

__all__ = [
    "UserProfile",
    "PasskeyCredential",
    "FailedLoginAttempt",
    "LoginAuditLog",
    "RSAKeyPair",
]
