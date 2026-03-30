#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate

echo "Checking/Creating superuser..."
python manage.py initadmin

echo "Starting Gunicorn..."
exec gunicorn --bind :8080 \
    --workers "${GUNICORN_WORKERS:-1}" \
    --threads "${GUNICORN_THREADS:-8}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    core.wsgi:application
