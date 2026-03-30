"""
Authentication and password settings.
"""

from datetime import timedelta

from core.settings.base import TESTING, SECRET_KEY, env

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # noqa: E501
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"  # noqa: E501
    },
]

# Prefer Argon2; keep PBKDF2 variants as fallback for compatibility
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Allow users with is_active=False to authenticate (pending activation flow)
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.AllowAllUsersModelBackend",
]

SIMPLE_JWT = {
    # Tests: keep tokens long to avoid flakiness; Prod: short-lived access,
    # moderate refresh
    "ACCESS_TOKEN_LIFETIME": (
        timedelta(days=1)
        if TESTING
        else timedelta(minutes=int(env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", "30")))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=1 if TESTING else int(env("JWT_REFRESH_TOKEN_LIFETIME_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    # Allow inactive (pending activation) users to obtain and use tokens
    "USER_AUTHENTICATION_RULE": "authn.authentication.allow_all_users_rule",
    "CHECK_USER_IS_ACTIVE": False,
}

AUTH_EXPOSE_TOKENS_IN_BODY = (
    env("AUTH_EXPOSE_TOKENS_IN_BODY", "False").lower() == "true"
)
