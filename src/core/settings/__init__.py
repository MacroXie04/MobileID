"""
Django settings module for core project.

This module automatically selects the appropriate settings based on:
1. DJANGO_SETTINGS_MODULE environment variable (highest priority)
2. DEBUG=False and TESTING=False in .env (auto-selects production)
3. Defaults to development settings

Usage:
    - Explicit: DJANGO_SETTINGS_MODULE=core.settings.dev
    - Auto (via .env): DEBUG=False TESTING=False -> production
    - Default: development settings
"""

import os

# Determine which settings to use based on environment variable
settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")

# If DJANGO_SETTINGS_MODULE is explicitly set, use it
if settings_module.endswith(".prod") or settings_module.endswith(
    ".production"
):
    from .prod import *  # noqa: F403, F401
elif settings_module.endswith(".dev") or settings_module.endswith(
    ".development"
):
    from .dev import *  # noqa: F403, F401
else:
    # Auto-detect based on DEBUG and TESTING environment variables
    # If DEBUG=False and TESTING=False, use production settings
    debug = os.environ.get("DEBUG", "True").lower() == "true"
    testing = os.environ.get("TESTING", "False").lower() == "true"

    if not debug and not testing:
        # Production mode: DEBUG=False and TESTING=False
        from .prod import *  # noqa: F403, F401
    else:
        # Default to development settings
        from .dev import *  # noqa: F403, F401
