"""
Django system checks for the core app.

These checks run at startup (manage.py check, runserver, gunicorn) and
flag misconfigurations before they become silent production failures.
"""

import os

from django.conf import settings
from django.core.checks import Error, register


@register()
def check_cache_backend_for_multi_worker(app_configs, **kwargs):
    """
    Ensure LocMemCache is not used when multiple Gunicorn workers are
    configured. LocMemCache is per-process, so login challenge nonces
    and other cached values won't be shared across workers.
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
                    "and will cause login challenge nonces to fail across workers."
                ),
                id="core.E001",
            )
        )
    return errors
