#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-west-2}"
DUMP_FILE=""
DB_URL="${DATABASE_URL_AWS:-}"
DB_SECRET_NAME="${DB_SECRET_NAME:-}"
RDS_SG_ID="${RDS_SG_ID:-}"
TEMP_IMPORT_CIDR="${TEMP_IMPORT_CIDR:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dump)
      DUMP_FILE="$2"; shift 2 ;;
    --db-url)
      DB_URL="$2"; shift 2 ;;
    --db-secret-name)
      DB_SECRET_NAME="$2"; shift 2 ;;
    --rds-sg-id)
      RDS_SG_ID="$2"; shift 2 ;;
    --temp-cidr)
      TEMP_IMPORT_CIDR="$2"; shift 2 ;;
    *)
      echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$DUMP_FILE" ]]; then
  echo "Usage: $0 --dump <path/to/sql-or-sql.gz> [--db-url mysql://...] [--db-secret-name name] [--rds-sg-id sg-xxx --temp-cidr x.x.x.x/32]"
  exit 1
fi

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "Dump file not found: $DUMP_FILE"
  exit 1
fi

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

if [[ -z "$DB_URL" ]]; then
  echo "DATABASE_URL_AWS is required (env --db-url or --db-secret-name)."
  exit 1
fi

if ! command -v mysql >/dev/null 2>&1; then
  echo "mysql client not found. Install mysql client first."
  exit 1
fi

IFS=$'\t' read -r DB_HOST DB_PORT DB_USER DB_PASS DB_NAME < <(python3 - <<'PY' "$DB_URL"
from urllib.parse import urlparse, unquote
import sys
u=urlparse(sys.argv[1])
print(
    u.hostname or "",
    u.port or 3306,
    unquote(u.username or ""),
    unquote(u.password or ""),
    (u.path or "/").lstrip("/"),
    sep="\t",
)
PY
)

if [[ -z "$DB_HOST" || -z "$DB_USER" || -z "$DB_PASS" || -z "$DB_NAME" ]]; then
  echo "Could not parse DB URL"
  exit 1
fi

cleanup_ingress() {
  if [[ -n "$RDS_SG_ID" && -n "$TEMP_IMPORT_CIDR" ]]; then
    aws ec2 revoke-security-group-ingress --group-id "$RDS_SG_ID" --protocol tcp --port 3306 --cidr "$TEMP_IMPORT_CIDR" >/dev/null 2>&1 || true
  fi
}
trap cleanup_ingress EXIT

if [[ -n "$RDS_SG_ID" && -n "$TEMP_IMPORT_CIDR" ]]; then
  echo "Temporarily authorizing $TEMP_IMPORT_CIDR on $RDS_SG_ID for import..."
  aws ec2 authorize-security-group-ingress --group-id "$RDS_SG_ID" --protocol tcp --port 3306 --cidr "$TEMP_IMPORT_CIDR" >/dev/null 2>&1 || true
fi

echo "Importing $DUMP_FILE into $DB_HOST:$DB_PORT/$DB_NAME ..."

if [[ "$DUMP_FILE" == *.gz ]]; then
  gunzip -c "$DUMP_FILE" | MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP --default-character-set=utf8mb4
else
  MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP --default-character-set=utf8mb4 < "$DUMP_FILE"
fi

echo "Running quick validations..."
MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP -N -e "USE ${DB_NAME}; SHOW TABLES;" | head -n 5
MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP -N -e "USE ${DB_NAME}; SELECT COUNT(*) AS django_migrations_count FROM django_migrations;"
MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP -N -e "USE ${DB_NAME}; SELECT COUNT(*) AS auth_user_count FROM auth_user;"
MYSQL_PWD="$DB_PASS" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --protocol=TCP -N -e "USE ${DB_NAME}; SELECT COUNT(*) AS login_audit_count FROM authn_loginauditlog;"

echo "Import complete."
