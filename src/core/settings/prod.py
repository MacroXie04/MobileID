"""
Production Django settings for core project.

This file imports base settings and overrides them with production-specific values.
"""

from .base import *  # noqa: F403, F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", "False").lower() == "true"
ENVIRONMENT = env("ENVIRONMENT", "production").lower()
IS_PRODUCTION = True

# SECURITY WARNING: keep the secret key used in production secret!
# Production MUST set SECRET_KEY via environment variable
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "dev-secret":
    raise ValueError(
        "SECRET_KEY must be set in production environment. "
        "Do not use the default dev-secret key!"
    )

# Hosts - MUST be set via environment variable in production
ALLOWED_HOSTS = csv_env("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ValueError(
        "ALLOWED_HOSTS must be set in production environment. "
        "This setting is required for security."
    )

# Production CORS origins - MUST be set via environment variable
FRONTEND_ORIGINS_PROD = csv_env("CORS_ALLOWED_ORIGINS")
if not FRONTEND_ORIGINS_PROD:
    raise ValueError(
        "CORS_ALLOWED_ORIGINS must be set in production environment. "
        "This setting is required for CORS to work properly."
    )

FRONTEND_ORIGINS = FRONTEND_ORIGINS_PROD

# Django 5 requires scheme://host[:port]
CSRF_TRUSTED_ORIGINS = csv_env(
    "CSRF_TRUSTED_ORIGINS", [BACKEND_ORIGIN, *FRONTEND_ORIGINS]
)

# If using django-cors-headers:
CORS_ALLOWED_ORIGINS = FRONTEND_ORIGINS
CORS_ALLOW_CREDENTIALS = env("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"

# Cookies - Production: secure cookies required
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", "True").lower() == "true"
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", "True").lower() == "true"
CSRF_COOKIE_HTTPONLY = False

# Security settings - Production: strict security
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", "True").lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "63072000"))  # 2 years
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "SAMEORIGIN"
CSP_DEFAULT_POLICY = env(
    "CSP_DEFAULT_POLICY",
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:",
)

# Production logging - structured logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "format": '{"time": "{asctime}", "level": "{levelname}", "module": "{module}", "message": "{message}"}',
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
        "level": env("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
