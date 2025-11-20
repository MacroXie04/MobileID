"""
Development Django settings for core project.

This file imports base settings and overrides them with development-specific values.  # noqa: E501
"""

from .base import *  # noqa: F403, F401
from .base import env, csv_env, BACKEND_ORIGIN  # noqa: F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", "True").lower() == "true"
ENVIRONMENT = env("ENVIRONMENT", "development").lower()
IS_PRODUCTION = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", "dev-secret-key-change-in-production")

# Hosts (localhost for development)
ALLOWED_HOSTS = csv_env("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

# Development CORS origins
FRONTEND_ORIGINS_DEV = csv_env(
    "CORS_ALLOWED_ORIGINS_DEV",
    [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
)

FRONTEND_ORIGINS = FRONTEND_ORIGINS_DEV

# Django 5 requires scheme://host[:port]
CSRF_TRUSTED_ORIGINS = csv_env(
    "CSRF_TRUSTED_ORIGINS", [BACKEND_ORIGIN, *FRONTEND_ORIGINS]
)

# If using django-cors-headers:
CORS_ALLOWED_ORIGINS = FRONTEND_ORIGINS
CORS_ALLOW_CREDENTIALS = (
    env("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
)

# Cookies - Development: insecure cookies allowed
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

# Security settings - Development: relaxed security
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 0  # Disable HSTS in development
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "SAMEORIGIN"
CSP_DEFAULT_POLICY = env(
    "CSP_DEFAULT_POLICY",
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: http: https:;",  # noqa: E501
)

# Development logging - more verbose
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",  # noqa: E501
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
