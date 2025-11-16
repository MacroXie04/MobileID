#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import warnings

# Suppress cbor2 deprecation warning (comes from third-party dependency)
# Must be done before Django imports to catch early warnings
warnings.filterwarnings("ignore", category=UserWarning, module="cbor2")


def main():
    """Run administrative tasks."""
    # Set default settings module - use main settings for all operations including tests
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mobileid.settings")

    # Set testing flag when running tests
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        os.environ.setdefault("TESTING", "True")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
