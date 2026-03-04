# Operations

## Deployment

- **Backend**: Deployed to AWS ECS Fargate via `aws_backend_deploy.yml`
- **Frontend**: Deployed to AWS Amplify via `aws_frontend_deploy.yml`

## Infrastructure Scripts

Scripts in `infra/aws/`:

- `bootstrap_resources.sh` — Provision AWS resources (ECR, ECS, RDS, etc.)
- `import_mysql_dump.sh` — Import database dumps into RDS
- `verify_migration.sh` — Verify database migrations after deployment

## Environment Variables

See `src/.env.example` for all available configuration options.

## Key Production Settings

- `AUTH_EXPOSE_TOKENS_IN_BODY=False` — Tokens only in HttpOnly cookies
- `ADMIN_URL_PATH` — Must be set to a non-default value
- `CSRF_TRUSTED_ORIGINS` — Required for CSRF validation
- `CORS_ALLOWED_ORIGINS` — Required for cross-origin requests
