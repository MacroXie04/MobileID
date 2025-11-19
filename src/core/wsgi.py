"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import warnings

# Suppress cbor2 deprecation warning (comes from third-party dependency)
# Must be done before Django imports to catch early warnings
warnings.filterwarnings("ignore", category=UserWarning, module="cbor2")

from django.core.wsgi import get_wsgi_application  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")

application = get_wsgi_application()
