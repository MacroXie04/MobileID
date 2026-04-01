#!/usr/bin/env python3
"""Render the ECS task definition template from environment variables."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

PLACEHOLDER_TO_ENV = {
    "__TASK_FAMILY__": "TASK_FAMILY",
    "__EXECUTION_ROLE_ARN__": "EXECUTION_ROLE_ARN",
    "__TASK_ROLE_ARN__": "TASK_ROLE_ARN",
    "__IMAGE__": "IMAGE_URI",
    "__AWS_REGION__": "AWS_REGION",
    "__DYNAMODB_TABLE_PREFIX__": "DYNAMODB_TABLE_PREFIX",
    "__BACKEND_ORIGIN__": "BACKEND_ORIGIN",
    "__ALLOWED_HOSTS__": "ALLOWED_HOSTS",
    "__CORS_ALLOWED_ORIGINS__": "CORS_ALLOWED_ORIGINS",
    "__CSRF_TRUSTED_ORIGINS__": "CSRF_TRUSTED_ORIGINS",
    "__ADMIN_URL_PATH__": "ADMIN_URL_PATH",
    "__SECRET_KEY_ARN__": "SECRET_KEY_ARN",
    "__DJANGO_SUPERUSER_USERNAME__": "DJANGO_SUPERUSER_USERNAME",
    "__DJANGO_SUPERUSER_EMAIL__": "DJANGO_SUPERUSER_EMAIL",
    "__DJANGO_SUPERUSER_PASSWORD_ARN__": "DJANGO_SUPERUSER_PASSWORD_ARN",
    "__DB_ENGINE__": "DB_ENGINE",
    "__DB_NAME__": "DB_NAME",
    "__PERSISTENCE_MODE__": "PERSISTENCE_MODE",
    "__RUN_DATABASE_MIGRATIONS__": "RUN_DATABASE_MIGRATIONS",
    "__RUN_INITADMIN__": "RUN_INITADMIN",
    "__EFS_FILE_SYSTEM_ID__": "EFS_FILE_SYSTEM_ID",
    "__EFS_ACCESS_POINT_ID__": "EFS_ACCESS_POINT_ID",
    "__LOG_GROUP__": "LOG_GROUP",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    template = args.template.read_text(encoding="utf-8")

    missing = sorted(
        env_name
        for env_name in PLACEHOLDER_TO_ENV.values()
        if not os.environ.get(env_name, "").strip()
    )
    if missing:
        raise SystemExit(
            "Missing required environment variables for task definition rendering: "
            + ", ".join(missing)
        )

    rendered = template
    for placeholder, env_name in PLACEHOLDER_TO_ENV.items():
        value = os.environ[env_name]
        rendered = rendered.replace(f'"{placeholder}"', json.dumps(value))

    unresolved = sorted(set(re.findall(r"__[A-Z0-9_]+__", rendered)))
    if unresolved:
        raise SystemExit(
            "Task definition still contains unresolved placeholders: "
            + ", ".join(unresolved)
        )

    parsed = json.loads(rendered)
    args.output.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
