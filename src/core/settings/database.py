"""
Database configuration for Django.

Supports multiple providers (local SQLite/PostgreSQL/MySQL, GCP Cloud SQL, AWS RDS)
via the DB_PROFILE environment variable and DATABASE_URL_* connection strings.
"""

import os

import dj_database_url

from core.settings.base import TESTING

# --- DB profile switch ---
# DB_PROFILE: "local", "gcp", or "aws" (or any custom name you like)
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
        engine = str(db_cfg.get("ENGINE", "")).lower()
        db_cfg.setdefault("OPTIONS", {})
        if "postgresql" in engine:
            db_cfg["OPTIONS"]["sslmode"] = DB_SSL_MODE
            if DB_DISABLE_SERVER_CERT_VERIFICATION:
                # psycopg: sslrootcert='' + sslmode=require will skip verification
                db_cfg["OPTIONS"]["sslmode"] = "require"
        elif "mysql" in engine:
            # mysqlclient enables TLS if ssl option exists
            db_cfg["OPTIONS"].setdefault("ssl", {})
    return db_cfg


def _from_url(url_env_name: str, default_url: str = "") -> dict:
    url = os.getenv(url_env_name, default_url)
    if not url:
        return {}
    cfg = dj_database_url.parse(
        url,
        conn_max_age=DB_CONN_MAX_AGE,
        ssl_require=(DB_SSL_MODE == "require"),
    )
    # dj-database-url may inject postgres-style sslmode for MySQL when
    # ssl_require is enabled. mysqlclient rejects that keyword.
    engine = str(cfg.get("ENGINE", "")).lower()
    if "mysql" in engine:
        cfg.setdefault("OPTIONS", {})
        cfg["OPTIONS"].pop("sslmode", None)
    return _apply_common(cfg)


DATABASES = {}

# Check if running in Google Cloud Run
if os.environ.get("K_SERVICE"):
    # Cloud Run (PostgreSQL via Cloud SQL Auth Proxy)
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": f"/cloudsql/{os.environ.get('INSTANCE_CONNECTION_NAME')}",
        "USER": os.environ.get("DB_USER"),
        "NAME": os.environ.get("DB_NAME"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
    }
else:
    # Local development or other environments
    # 1) Prefer explicit URL for the chosen profile
    #    - For local MySQL, set DATABASE_URL_LOCAL like:
    #      mysql://user:pass@127.0.0.1:3306/dbname
    #    - For local Postgres: postgres://user:pass@127.0.0.1:5432/dbname
    #    - For GCP/Cloud SQL TCP: same postgres/mysql URL pointing to the Cloud SQL
    #      proxy IP or public IP
    #    - For GCP/Cloud SQL Unix socket:
    #        postgres:  postgres://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE  # noqa: E501
    #        mysql:     mysql://user:pass@/dbname?unix_socket=/cloudsql/PROJECT:REGION:INSTANCE  # noqa: E501
    profile_to_env = {
        "local": "DATABASE_URL_LOCAL",
        "gcp": "DATABASE_URL_GCP",
        "aws": "DATABASE_URL_AWS",
    }

    db_cfg = _from_url(profile_to_env.get(DB_PROFILE, "DATABASE_URL"))
    if not db_cfg and DB_PROFILE not in profile_to_env:
        db_cfg = _from_url("DATABASE_URL")
    if not db_cfg:
        # 2) Fallback to legacy discrete vars (DB_ENGINE, DB_NAME, DB_USER,
        # DB_PASSWORD, DB_HOST, DB_PORT)
        default_engine = "mysql" if DB_PROFILE in {"gcp", "aws"} else "postgresql"
        ENGINE = os.getenv("DB_ENGINE", default_engine).lower()
        if ENGINE in {
            "postgres",
            "postgresql",
            "psql",
            "django.db.backends.postgresql",
        }:
            engine_path = "django.db.backends.postgresql"
        elif ENGINE in {"mysql", "django.db.backends.mysql"}:
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
        instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME", "")
        unix_socket = os.getenv("CLOUDSQL_UNIX_SOCKET", "")
        if DB_PROFILE == "gcp" and instance_connection_name and not unix_socket:
            unix_socket = f"/cloudsql/{instance_connection_name}"

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
                options["ssl"] = {}

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

    DATABASES["default"] = db_cfg

# Use SQLite for tests, configured database for everything else
if TESTING:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # Use in-memory database for tests
    }
