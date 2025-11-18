"""
Django settings module for core project.

This module automatically selects the appropriate settings based on the
DJANGO_SETTINGS_MODULE environment variable or defaults to development.

Usage:
    - Development: DJANGO_SETTINGS_MODULE=core.settings.dev
    - Production: DJANGO_SETTINGS_MODULE=core.settings.prod
"""

import os

# Determine which settings to use based on environment variable
# Default to development if not specified
settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")

if settings_module.endswith(".prod") or settings_module.endswith(".production"):
    from .prod import *  # noqa: F403, F401
elif settings_module.endswith(".dev") or settings_module.endswith(".development"):
    from .dev import *  # noqa: F403, F401
else:
    # Default to development settings
    from .dev import *  # noqa: F403, F401
