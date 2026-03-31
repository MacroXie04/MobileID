#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install -r src/requirements.txt

echo "Collecting static files..."
cd src
SECRET_KEY=build-only python manage.py collectstatic --noinput

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Creating cache table..."
python manage.py createcachetable || true

echo "Build complete."
