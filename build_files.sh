#!/bin/bash
set -e

cd src

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Running database migrations..."
python3 manage.py migrate --noinput

echo "Creating cache table..."
python3 manage.py createcachetable || true

echo "Creating/updating superuser..."
python3 manage.py initadmin || true

echo "Build complete."
