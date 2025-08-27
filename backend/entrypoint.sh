#!/usr/bin/env bash
set -euo pipefail

echo "Starting MobileID Backend..."

# Allow choosing env file path; default to .env
ENV_FILE="${ENV_FILE:-/app/.env}"
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment from $ENV_FILE"
  set -a
  . "$ENV_FILE"
  set +a
else
  echo "Warning: Environment file $ENV_FILE not found"
fi

# Ensure src is on PYTHONPATH
export PYTHONPATH="/app/src:${PYTHONPATH:-}"

# Wait for database to be ready (MySQL)
echo "Waiting for database to be ready..."
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"

# If DB_HOST is host.docker.internal, skip the wait (for local development)
if [ "$DB_HOST" != "host.docker.internal" ]; then
  until nc -z "$DB_HOST" "$DB_PORT"; do
    echo "Database is unavailable - sleeping"
    sleep 1
  done
  echo "Database is up - executing command"
fi

# Collect static files
echo "Collecting static files..."
python /app/manage.py collectstatic --noinput || true

# Run database migrations
echo "Running database migrations..."
python /app/manage.py migrate --noinput

# Create superuser if environment variables are set
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  echo "Creating superuser..."
  python /app/manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME}').exists():
    User.objects.create_superuser('${DJANGO_SUPERUSER_USERNAME}', '${DJANGO_SUPERUSER_EMAIL}', '${DJANGO_SUPERUSER_PASSWORD}')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
" || echo "Could not create superuser"
fi

echo "Starting application server..."

# Start ASGI app with proper configuration
exec gunicorn mobileid.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --keep-alive "${GUNICORN_KEEPALIVE:-5}" \
  --max-requests "${GUNICORN_MAX_REQUESTS:-1000}" \
  --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-100}" \
  --access-logfile - \
  --error-logfile -


