#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate

echo "Checking/Creating superuser..."
python manage.py initadmin

echo "Starting Gunicorn..."
exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 core.wsgi:application

