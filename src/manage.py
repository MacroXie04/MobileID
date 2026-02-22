#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks."""
    # Set default settings module - use dev settings for development
    # Override with DJANGO_SETTINGS_MODULE env var for production
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")

    # Set testing flag when running tests
    # Force-set (not setdefault) to ensure it overrides any existing value
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        os.environ["TESTING"] = "True"

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
