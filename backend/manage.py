#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

import dotenv


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "barcode.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


def print_env():
    print("Environment variables:")
    print("DEBUG: ", os.getenv("DEBUG"))
    print("ALLOWED_HOSTS: ", os.getenv("ALLOWED_HOSTS"))
    print("DATABASE_URL: ", os.getenv("DATABASE_URL"))
    print("EMAIL_HOST: ", os.getenv("EMAIL_HOST"))
    print("EMAIL_PORT: ", os.getenv("EMAIL_PORT"))
    print("EMAIL_HOST_USER: ", os.getenv("EMAIL_HOST_USER"))
    print("EMAIL_HOST_PASSWORD: ", os.getenv("EMAIL_HOST_PASSWORD"))


if __name__ == "__main__":
    print_env()
    main()
