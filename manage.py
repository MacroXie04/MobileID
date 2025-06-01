#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ucm_barcode.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Check if runserver command is being used
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        # Check if SSL certificates exist, if not generate them
        ssl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl')
        cert_path = os.path.join(ssl_dir, 'localhost.crt')
        key_path = os.path.join(ssl_dir, 'localhost.key')

        if not (os.path.exists(cert_path) and os.path.exists(key_path)):
            print("SSL certificates not found. Generating self-signed certificates...")
            cert_script = os.path.join(ssl_dir, 'generate_cert.sh')
            if os.path.exists(cert_script):
                os.system(f"bash {cert_script}")
            else:
                print("Certificate generation script not found. Please run ssl/generate_cert.sh manually.")

        # Add SSL parameters to runserver command
        sys.argv.append('--cert')
        sys.argv.append(cert_path)
        sys.argv.append('--key')
        sys.argv.append(key_path)

        print("Starting development server with HTTPS support...")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
