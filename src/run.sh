#!/bin/bash
set -e

echo "Running migrations..."
uv run python manage.py migrate

echo "Checking/Creating superuser..."
uv run python manage.py initadmin

echo "Checking/Generating RSA key pair..."
uv run python manage.py generate_rsa_keypair --if-not-exists

echo "Starting Gunicorn..."
exec uv run gunicorn --bind :8080 --workers 1 --threads 8 --timeout 120 core.wsgi:application

