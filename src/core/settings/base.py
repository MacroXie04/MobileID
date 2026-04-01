"""
Base Django settings for core project.

This file contains all common settings shared between development and production.
Environment-specific settings are defined in dev.py and prod.py.

Settings are split across multiple files for organization:
- base.py: Core Django configuration (this file)
- database.py: Database connection configuration
- auth.py: Authentication and password settings
- security.py: Security, caching, session, and throttling settings
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Prefer real env vars; then supplement from .env if present (do NOT override)
load_dotenv(BASE_DIR / ".env", override=False)


def env(key, default=None):
    return os.environ.get(key, default)


def csv_env(key, default_list=None):
    raw = env(key)
    if not raw:
        return default_list or []
    return [x.strip() for x in raw.split(",") if x.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
# This will be overridden in dev.py and prod.py
SECRET_KEY = env("SECRET_KEY", "dev-secret")

# Test environment detection
# Check environment variable first, then fall back to sys.argv check
TESTING = os.getenv("TESTING", "False").lower() == "true"
if not TESTING:
    # Also detect if running via Django test command
    import sys

    TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

INSTALLED_APPS = [
    # index app
    "index.apps.IndexConfig",
    # user authentication
    "authn.apps.AuthnConfig",
    # core app (must be before admin for admin registration)
    "core.apps.CoreConfig",
    # Django REST framework
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework.authtoken",
    "corsheaders",
    # modules
    "widget_tweaks",
    "django_extensions",
    # Default Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# Additional locations to look for static files during development
# Note: STATICFILES_DIRS should NOT include STATIC_ROOT
STATICFILES_DIRS = [
    BASE_DIR / "core" / "static",
]

# Static files finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MIDDLEWARE = [
    # CORS middleware must be placed before Django's security middleware
    "corsheaders.middleware.CorsMiddleware",
    # Default Django middleware
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.admin_security.AdminIPWhitelistMiddleware",
    "core.middleware.admin_security.AdminLoginThrottleMiddleware",
    "core.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.admin_security.AdminSessionExpiryMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.admin_audit.AdminAuditMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

BACKEND_ORIGIN = env("BACKEND_ORIGIN", "http://localhost:8000")

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = env("TIME_ZONE", "America/Los_Angeles")

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Use custom test runner that sets up moto-mocked DynamoDB
TEST_RUNNER = "core.test_runner.DynamoDBTestRunner"

# Import settings from sub-modules
from core.settings.database import *  # noqa: E402, F401, F403
from core.settings.auth import *  # noqa: E402, F401, F403
from core.settings.security import *  # noqa: E402, F401, F403
from core.settings.dynamodb import *  # noqa: E402, F401, F403
