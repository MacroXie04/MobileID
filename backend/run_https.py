#!/usr/bin/env python
import os
import sys

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "barcode.settings")

# Run the server with SSL support
if __name__ == "__main__":
    print("Starting HTTPS server on https://localhost:8000")
    print("You can also access it via https://127.0.0.1:8000")
    print("Press Ctrl+C to stop")

    # Use django-extensions' runserver_plus with SSL support
    from django.core.management import execute_from_command_line

    execute_from_command_line(
        [
            "manage.py",
            "runserver_plus",
            "--cert-file",
            "cert.pem",
            "--key-file",
            "key.pem",
            "0.0.0.0:8000",
        ]
    )
