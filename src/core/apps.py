"""
Core app configuration.
"""

import os

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, register


@register()
def check_cache_backend_for_multi_worker(app_configs, **kwargs):
    """
    Ensure LocMemCache is not used when multiple Gunicorn workers are
    configured. LocMemCache is per-process, so throttle counters,
    session state, and other cached values won't be shared across workers.
    """
    errors = []
    workers = int(os.getenv("GUNICORN_WORKERS", "1"))
    cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "")

    if workers > 1 and "LocMemCache" in cache_backend:
        errors.append(
            Error(
                "LocMemCache is incompatible with multiple Gunicorn workers.",
                hint=(
                    "Set CACHE_BACKEND to a shared backend "
                    "(e.g. django.core.cache.backends.db.DatabaseCache) "
                    "when GUNICORN_WORKERS > 1. LocMemCache is per-process "
                    "and will cause throttle counters and session state to diverge across workers."
                ),
                id="core.E001",
            )
        )
    return errors


class CoreConfig(AppConfig):
    """Configuration for core app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core"

    def ready(self):
        """Import admin registration and connect signals when app is ready"""
        # Import admin to register models
        import core.admin  # noqa: F401

        # Connect admin login/logout logging signals
        self._connect_admin_signals()

    def _connect_admin_signals(self):
        """Connect signal handlers for admin login/logout auditing."""
        from django.contrib.auth.signals import user_logged_in, user_logged_out

        from core.middleware.admin_audit import log_admin_login, log_admin_logout

        def handle_admin_login(sender, request, user, **kwargs):
            if user.is_staff and request and hasattr(request, "path"):
                admin_path = f"/{settings.ADMIN_URL_PATH}/"
                if request.path.startswith(admin_path):
                    log_admin_login(request, user, success=True)

        def handle_admin_logout(sender, request, user, **kwargs):
            if user and user.is_staff and request and hasattr(request, "path"):
                admin_path = f"/{settings.ADMIN_URL_PATH}/"
                if request.path.startswith(admin_path):
                    log_admin_logout(request, user)

        user_logged_in.connect(handle_admin_login, dispatch_uid="admin_login_audit")
        user_logged_out.connect(handle_admin_logout, dispatch_uid="admin_logout_audit")
