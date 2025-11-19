"""
Base Django settings for core project.

This file contains all common settings shared between development and production.
Environment-specific settings are defined in dev.py and prod.py.
"""

import os
import warnings
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Prefer real env vars; then supplement from .env if present (do NOT override)
load_dotenv(BASE_DIR / ".env", override=False)

# Suppress cbor2 deprecation warning (comes from third-party dependency)
warnings.filterwarnings("ignore", category=UserWarning, module="cbor2")


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
TESTING = os.getenv("TESTING", "False").lower() == "true"

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

# Additional locations to look for static files during development
# Note: STATICFILES_DIRS should NOT include STATIC_ROOT
STATICFILES_DIRS = [
    # Add paths to additional static files directories here
    # Example: BASE_DIR / "assets",
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
    "core.middleware.admin_ip_whitelist.AdminIPWhitelistMiddleware",
    "core.middleware.admin_throttle.AdminLoginThrottleMiddleware",
    "core.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.admin_session.AdminSessionExpiryMiddleware",
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
        "DIRS": [],
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

# Database (profile-based configuration)
# --- DB profile switch ---
# DB_PROFILE: "local" or "gcp" (or any custom name you like)
DB_PROFILE = os.getenv("DB_PROFILE", "local").lower()

# Common options
DB_CONN_MAX_AGE = int(os.getenv("DB_CONN_MAX_AGE", "60"))  # persistent connections
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "").lower()  # "", "require", "verify-full"
DB_DISABLE_SERVER_CERT_VERIFICATION = (
    os.getenv("DB_SSL_DISABLE_VERIFY", "false").lower() == "true"
)


def _apply_common(db_cfg: dict) -> dict:
    db_cfg.setdefault("CONN_MAX_AGE", DB_CONN_MAX_AGE)
    # SSL (useful for Cloud SQL / managed DBs)
    if DB_SSL_MODE in {"require", "verify-ca", "verify-full"}:
        db_cfg.setdefault("OPTIONS", {})
        db_cfg["OPTIONS"]["sslmode"] = DB_SSL_MODE
        if DB_DISABLE_SERVER_CERT_VERIFICATION:
            # psycopg: sslrootcert='' + sslmode=require will skip verification; for mysqlclient use 'ssl' dict
            db_cfg["OPTIONS"]["sslmode"] = "require"
    return db_cfg


def _from_url(url_env_name: str, default_url: str = "") -> dict:
    url = os.getenv(url_env_name, default_url)
    if not url:
        return {}
    cfg = dj_database_url.parse(
        url, conn_max_age=DB_CONN_MAX_AGE, ssl_require=(DB_SSL_MODE == "require")
    )
    return _apply_common(cfg)


DATABASES = {}

# 1) Prefer explicit URL for the chosen profile
#    - For local MySQL, set DATABASE_URL_LOCAL like: mysql://user:pass@127.0.0.1:3306/dbname
#    - For local Postgres: postgres://user:pass@127.0.0.1:5432/dbname
#    - For GCP/Cloud SQL TCP: same postgres/mysql URL pointing to the Cloud SQL proxy IP or public IP
#    - For GCP/Cloud SQL Unix socket:
#        postgres:  postgres://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
#        mysql:     mysql://user:pass@/dbname?unix_socket=/cloudsql/PROJECT:REGION:INSTANCE
profile_to_env = {
    "local": "DATABASE_URL_LOCAL",
    "gcp": "DATABASE_URL_GCP",
}

db_cfg = _from_url(profile_to_env.get(DB_PROFILE, "DATABASE_URL"))
if not db_cfg:
    # 2) Fallback to legacy discrete vars (DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    ENGINE = os.getenv("DB_ENGINE", "postgresql").lower()
    if ENGINE in {"postgres", "postgresql", "psql"}:
        engine_path = "django.db.backends.postgresql"
    elif ENGINE in {"mysql"}:
        engine_path = "django.db.backends.mysql"
    else:
        engine_path = "django.db.backends.sqlite3"

    host = os.getenv("DB_HOST", "")
    port = os.getenv("DB_PORT", "")
    name = os.getenv("DB_NAME", "")
    user = os.getenv("DB_USER", "")
    pwd = os.getenv("DB_PASSWORD", "")

    # Cloud SQL Unix socket override (if provided)
    # For Postgres: set CLOUDSQL_UNIX_SOCKET=/cloudsql/PROJECT:REGION:INSTANCE
    # For MySQL:   same var; django will pass via OPTIONS
    unix_socket = os.getenv("CLOUDSQL_UNIX_SOCKET", "")

    options = {}
    if unix_socket:
        if "postgresql" in engine_path:
            # psycopg uses host=/cloudsql/instance to connect via socket
            host = unix_socket
        elif "mysql" in engine_path:
            options["unix_socket"] = unix_socket

    if DB_SSL_MODE in {"require", "verify-ca", "verify-full"}:
        if "postgresql" in engine_path:
            options["sslmode"] = DB_SSL_MODE
        elif "mysql" in engine_path:
            options["ssl"] = {"ssl-mode": DB_SSL_MODE}

    db_cfg = {
        "ENGINE": engine_path,
        "NAME": name,
        "USER": user,
        "PASSWORD": pwd,
        "HOST": host or None,
        "PORT": port or None,
        "OPTIONS": options or {},
        "CONN_MAX_AGE": DB_CONN_MAX_AGE,
    }

# Use SQLite for tests, configured database for everything else
if TESTING:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # Use in-memory database for tests
    }
else:
    DATABASES["default"] = db_cfg

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Prefer Argon2; keep PBKDF2 variants as fallback for compatibility
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = env("TIME_ZONE", "America/Los_Angeles")

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Account security settings
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
ACCOUNT_LOCKOUT_DURATION = int(os.getenv("ACCOUNT_LOCKOUT_DURATION", "30"))

# Cache configuration
# Use only local memory cache and database session backend (no Redis support)
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

# Session settings - Set to 10 years (effectively unlimited)
SESSION_COOKIE_AGE = 315360000  # 10 years in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keep session alive even after browser close
SESSION_SAVE_EVERY_REQUEST = True  # Update session expiry on each request

# CORS settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "authn.middleware.authentication.CookieJWTAuthentication",
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
        "login_username": "5/15min",
        "registration": "5/day",
        "barcode_generation": "100/hour",
        "barcode_management": "50/hour",
        "user_profile": "20/hour",
        "admin_login": "5/15min",
    },
}

SIMPLE_JWT = {
    # Tests: keep tokens long to avoid flakiness; Prod: short-lived access, moderate refresh
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1) if TESTING else timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=1 if TESTING else int(env("JWT_REFRESH_TOKEN_LIFETIME_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

LOGIN_CHALLENGE_TTL_SECONDS = int(env("LOGIN_CHALLENGE_TTL_SECONDS", "120"))
LOGIN_CHALLENGE_NONCE_BYTES = int(env("LOGIN_CHALLENGE_NONCE_BYTES", "16"))

# Admin security settings
ADMIN_URL_PATH = env("ADMIN_URL_PATH", "admin")
ADMIN_ALLOWED_IPS = csv_env("ADMIN_ALLOWED_IPS", [])
ADMIN_SESSION_COOKIE_AGE = int(env("ADMIN_SESSION_COOKIE_AGE", "7200"))  # 2 hours

# Logging configuration
if TESTING:
    # Suppress warnings during testing to avoid noise from expected 4xx responses and dependencies
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
