#!/usr/bin/env bash
set -euo pipefail

# Allow choosing env file path; default to .env.development
ENV_FILE="${ENV_FILE:-/app/.env.development}"
if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

# Ensure src is on PYTHONPATH
export PYTHONPATH="/app/src:${PYTHONPATH:-}"

# Migrations (ok if no migrations yet)
python /app/manage.py migrate --noinput || true

# Start ASGI app
exec gunicorn mobileid.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}"


