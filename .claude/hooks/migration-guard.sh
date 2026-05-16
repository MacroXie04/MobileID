#!/usr/bin/env bash
# PreToolUse hook: block Edit/Write/MultiEdit on existing Django migration files.
# Mirrors the CI 'migration-file-guard' job — CI will reject PRs that modify
# prior migrations, so blocking locally saves a round-trip.
#
# Stdin is the PreToolUse JSON envelope; we read tool_input.file_path. We exit 2
# (the "block and surface stderr to Claude" code) iff the path is a tracked
# migration file. New migration files (untracked) are allowed.

set -u

input="$(cat)"

file_path="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(d.get("tool_input", {}).get("file_path", ""))
' 2>/dev/null || true)"

[ -z "$file_path" ] && exit 0

# Only consider files under src/<app>/migrations/*.py, excluding __init__.py.
case "$file_path" in
  */src/*/migrations/__init__.py|src/*/migrations/__init__.py) exit 0 ;;
  */src/*/migrations/*.py|src/*/migrations/*.py) ;;
  *) exit 0 ;;
esac

# Allow brand-new migration files (untracked); block edits to tracked ones.
if git ls-files --error-unmatch -- "$file_path" >/dev/null 2>&1; then
  echo "Blocked: '$file_path' is an existing migration file." >&2
  echo "CI 'migration-file-guard' rejects edits to prior migrations." >&2
  echo "Add a new migration on top instead: cd src && python manage.py makemigrations <app>" >&2
  exit 2
fi

exit 0
