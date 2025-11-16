"""
ASGI config for mobileid project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import warnings

# Suppress cbor2 deprecation warning (comes from third-party dependency)
# Must be done before Django imports to catch early warnings
warnings.filterwarnings("ignore", category=UserWarning, module="cbor2")

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mobileid.settings")

application = get_asgi_application()
