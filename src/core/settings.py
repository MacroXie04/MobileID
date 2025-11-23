"""
Legacy Django settings file for backward compatibility.

This file imports from core.settings.dev to maintain backward compatibility
with code that references core.settings directly.

For new code, use:
    - core.settings.dev for development
    - core.settings.prod for production
"""

# Import development settings for backward compatibility
from core.settings.dev import *
