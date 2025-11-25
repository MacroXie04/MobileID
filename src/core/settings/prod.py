"""
Production Django settings for core project.

This file imports base settings and overrides them with production-specific values.  # noqa: E501
"""

from .base import *  # noqa: F403, F401
from .base import env, csv_env, BACKEND_ORIGIN  # noqa: F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", "False").lower() == "true"
ENVIRONMENT = env("ENVIRONMENT", "production").lower()
IS_PRODUCTION = True

# Production: Enable throttles by default (override base.py default)
# Can be disabled with DISABLE_THROTTLES environment variable
if not env("DISABLE_THROTTLES"):
    DISABLE_THROTTLES = False
    THROTTLES_ENABLED = True

# Guarantee login username throttling is configured in production even if a
# downstream import accidentally wipes the scope (breaks Cloud Run login).
REST_FRAMEWORK.setdefault("DEFAULT_THROTTLE_RATES", {})
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].setdefault("login_username", "5/minute")

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

# Handle wildcard for CORS
if "*" in FRONTEND_ORIGINS_PROD or '["*"]' in FRONTEND_ORIGINS_PROD:
    CORS_ALLOW_ALL_ORIGINS = True
    FRONTEND_ORIGINS = []  # Don't add wildcard to CSRF trusted origins
else:
    CORS_ALLOW_ALL_ORIGINS = False
    FRONTEND_ORIGINS = FRONTEND_ORIGINS_PROD

if not FRONTEND_ORIGINS_PROD and not CORS_ALLOW_ALL_ORIGINS:
    raise ValueError(
        "CORS_ALLOWED_ORIGINS must be set in production environment. "
        "This setting is required for CORS to work properly."
    )

# Django 5 requires scheme://host[:port]
CSRF_TRUSTED_ORIGINS = csv_env(
    "CSRF_TRUSTED_ORIGINS", [BACKEND_ORIGIN, *FRONTEND_ORIGINS]
)

# If using django-cors-headers:
CORS_ALLOWED_ORIGINS = FRONTEND_ORIGINS if not CORS_ALLOW_ALL_ORIGINS else []
CORS_ALLOW_CREDENTIALS = env("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"

# Cookies - Production: secure cookies required
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False  # env("SESSION_COOKIE_SECURE", "True").lower() == "true"
CSRF_COOKIE_SECURE = False  # env("CSRF_COOKIE_SECURE", "True").lower() == "true"
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
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:",  # noqa: E501
)

# Admin security - Production: MUST be configured
ADMIN_URL_PATH = env("ADMIN_URL_PATH")
if not ADMIN_URL_PATH:
    print("WARNING: ADMIN_URL_PATH not set in production. Defaulting to 'admin'.")
    ADMIN_URL_PATH = "admin"
elif ADMIN_URL_PATH == "admin":
    print(
        "WARNING: ADMIN_URL_PATH set to default 'admin' in production. "
        "This is a security risk."
    )


ADMIN_ALLOWED_IPS = []  # Disable IP whitelist for now


# ---------------------------------------------------------------------
# Cloud SQL MySQL database configuration (Production)
# ---------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": "/cloudsql/" + env("INSTANCE_CONNECTION_NAME"),
        "PORT": "3306",
        "NAME": env("DB_NAME", "mobileid_prod"),
        "USER": env("DB_USER", "root"),
        "PASSWORD": env("DB_PASSWORD"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}


# Production logging - structured logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",  # noqa: E501
            "style": "{",
        },
        "json": {
            "format": '{{"time": "{asctime}", "level": "{levelname}", "module": "{module}", "message": "{message}"}}',  # noqa: E501
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
