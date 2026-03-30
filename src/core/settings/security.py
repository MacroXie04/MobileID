"""
Security, caching, session, throttling, and logging settings.
"""

import os

from core.settings.base import TESTING, env, csv_env

# Account security settings
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
ACCOUNT_LOCKOUT_DURATION = int(os.getenv("ACCOUNT_LOCKOUT_DURATION", "30"))

# Cache configuration
CACHE_BACKEND = os.getenv(
    "CACHE_BACKEND", "django.core.cache.backends.locmem.LocMemCache"
)
CACHE_LOCATION = os.getenv("CACHE_LOCATION", "unique-snowflake")

CACHES = {
    "default": {
        "BACKEND": CACHE_BACKEND,
        "LOCATION": CACHE_LOCATION,
    }
}
SESSION_ENGINE = os.getenv(
    "SESSION_ENGINE",
    (
        "django.contrib.sessions.backends.cache"
        if TESTING
        else "django.contrib.sessions.backends.db"
    ),
)

# Session settings - 30 days; JWT refresh tokens handle re-authentication
SESSION_COOKIE_AGE = 2592000  # 30 days in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keep session alive even after browser close
SESSION_SAVE_EVERY_REQUEST = (
    False  # JWT handles API auth; admin sessions use AdminSessionExpiryMiddleware
)

# Cookie security defaults (overridden in dev.py / prod.py)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False  # Overridden to True in prod.py
CSRF_COOKIE_SECURE = False  # Overridden to True in prod.py
CSRF_COOKIE_HTTPONLY = False  # Must be False so JS can read CSRF token
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "SAMEORIGIN"

# REST throttle settings
# Default to disabling throttles in development (when DEBUG=True) unless testing.
# Can be overridden with DISABLE_THROTTLES environment variable.
# Production overrides this in prod.py.
# Note: TESTING takes precedence - when running tests, throttles are always enabled
# to ensure security behavior is properly covered.
if TESTING:
    # Always keep throttles enabled when running tests
    DISABLE_THROTTLES = False
else:
    throttle_setting = env("DISABLE_THROTTLES")
    if throttle_setting not in (None, ""):
        DISABLE_THROTTLES = throttle_setting.lower() == "true"
    else:
        # Default to True (disable throttles) for development
        # Production should override this in prod.py
        DISABLE_THROTTLES = True
THROTTLES_ENABLED = not DISABLE_THROTTLES

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "authn.authentication.CookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "login": "5/minute",
        "login_username": "5/minute",
        "registration": "5/day",
        "refresh": "10/minute",
        "barcode_generation": "100/hour",
        "barcode_management": "50/hour",
        "user_profile": "20/hour",
        "admin_login": "5/15min",
    },
}

if DISABLE_THROTTLES:
    REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

# Security headers
PERMISSIONS_POLICY = env(
    "PERMISSIONS_POLICY",
    "camera=(*), microphone=(), geolocation=(), payment=()",
)
CROSS_ORIGIN_OPENER_POLICY = env("CROSS_ORIGIN_OPENER_POLICY", "same-origin")
CROSS_ORIGIN_RESOURCE_POLICY = env("CROSS_ORIGIN_RESOURCE_POLICY", "same-origin")
CSP_REPORT_ONLY = env("CSP_REPORT_ONLY", "False").lower() == "true"

# Admin security settings
ADMIN_URL_PATH = env("ADMIN_URL_PATH", "admin")
ADMIN_ALLOWED_IPS = csv_env("ADMIN_ALLOWED_IPS", [])
ADMIN_SESSION_COOKIE_AGE = int(env("ADMIN_SESSION_COOKIE_AGE", "7200"))  # 2 hours

# Logging configuration
if TESTING:
    # Suppress warnings during testing to avoid noise from expected 4xx
    # responses and dependencies
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "null": {
                "class": "logging.NullHandler",
            },
        },
        "loggers": {
            "django.request": {
                "handlers": ["null"],
                "level": "ERROR",  # Only show actual errors, not warnings
                "propagate": False,
            },
            "py.warnings": {
                "handlers": ["null"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }
