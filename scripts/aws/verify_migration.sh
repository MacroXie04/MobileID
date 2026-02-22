#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-west-2}"
DB_URL="${DATABASE_URL_AWS:-}"
DB_SECRET_NAME="${DB_SECRET_NAME:-}"
BACKEND_URL="${BACKEND_URL:-}"
FRONTEND_URL="${FRONTEND_URL:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-url)
      DB_URL="$2"; shift 2 ;;
    --db-secret-name)
      DB_SECRET_NAME="$2"; shift 2 ;;
    --backend-url)
      BACKEND_URL="$2"; shift 2 ;;
    --frontend-url)
      FRONTEND_URL="$2"; shift 2 ;;
    *)
      echo "Unknown arg: $1"; exit 1 ;;
  esac
done

aws() {
  command aws --region "$AWS_REGION" "$@"
}

if [[ -z "$DB_URL" && -n "$DB_SECRET_NAME" ]]; then
  secret_json="$(aws secretsmanager get-secret-value --secret-id "$DB_SECRET_NAME" --query 'SecretString' --output text)"
  DB_URL="$(python3 - <<'PY' "$secret_json"
import json,sys
s=json.loads(sys.argv[1])
print(s.get('DATABASE_URL_AWS',''))
PY
)"
fi

if [[ -n "$BACKEND_URL" ]]; then
  echo "Checking backend health: ${BACKEND_URL}/health/"
  code="$(curl -s -o /dev/null -w '%{http_code}' "${BACKEND_URL}/health/" || true)"
  if [[ "$code" != "200" ]]; then
    echo "Backend health check failed: HTTP $code"
    exit 1
  fi
fi

if [[ -n "$FRONTEND_URL" ]]; then
  echo "Checking frontend URL: ${FRONTEND_URL}"
  code="$(curl -s -o /dev/null -w '%{http_code}' "$FRONTEND_URL" || true)"
  if [[ "$code" -lt 200 || "$code" -ge 400 ]]; then
    echo "Frontend check failed: HTTP $code"
    exit 1
  fi
fi

if [[ -n "$DB_URL" ]]; then
  if ! command -v mysql >/dev/null 2>&1; then
    echo "mysql client not found. Skip DB checks."
    exit 0
  fi

  readarray -t parts < <(python3 - <<'PY' "$DB_URL"
from urllib.parse import urlparse, unquote
import sys
u=urlparse(sys.argv[1])
print(u.hostname or "")
print(u.port or 3306)
print(unquote(u.username or ""))
print(unquote(u.password or ""))
print((u.path or "/").lstrip("/"))
PY
)

  DB_HOST="${parts[0]}"
  DB_PORT="${parts[1]}"
  DB_USER="${parts[2]}"
  DB_PASS="${parts[3]}"
  DB_NAME="${parts[4]}"

  echo "Checking key table counts in ${DB_NAME}..."
  MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP -N -e "USE ${DB_NAME}; SELECT COUNT(*) AS django_migrations_count FROM django_migrations;"
  MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP -N -e "USE ${DB_NAME}; SELECT COUNT(*) AS auth_user_count FROM auth_user;"
  MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP -N -e "USE ${DB_NAME}; SELECT COUNT(*) AS login_audit_count FROM authn_loginauditlog;"
fi

echo "Verification checks passed."
