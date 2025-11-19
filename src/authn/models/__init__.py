# Import all models to maintain backward compatibility
from .failed_login_attempt import FailedLoginAttempt
from .login_audit import LoginAuditLog
from .passkey_credential import PasskeyCredential
from .rsa_keys import RSAKeyPair
from .user_profile import UserProfile

__all__ = [
    "UserProfile",
    "PasskeyCredential",
    "FailedLoginAttempt",
    "LoginAuditLog",
    "RSAKeyPair",
]
