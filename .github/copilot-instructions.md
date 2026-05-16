# Copilot instructions for MobileID

MobileID is a dual-stack app: Django REST backend in `src/`, Vue 3 + TypeScript SPA in `pages/`. See `CLAUDE.md` at the repo root for the full architecture guide.

## Backend (`src/`)
- Apps: `authn` (auth/JWT/WebAuthn/RSA), `index` (PDF417 barcodes, dashboards), `core` (config, middleware, settings, dynamodb).
- Layered: `api/`, `services/`, `repositories/`, `models/`, `serializers/`. Middleware only lives in `core/middleware/` — apps do not have their own `middleware/` subdirectory.
- Settings are split across `src/core/settings/{base,database,auth,security,dynamodb,dev,prod}.py`. Tests and CI use `DJANGO_SETTINGS_MODULE=core.settings.dev`.
- Code style: Black (line length 88) + Ruff + Flake8. Run all three before committing.
- **Migration discipline**: never edit an existing migration file. Add a new migration on top. CI's `migration-file-guard` rejects PRs that modify prior migrations. CI also runs `makemigrations --check`.
- DynamoDB-backed data (passkey credentials, RSA key material, security events) lives under `core/dynamodb/`, not in Django ORM models.
- Custom management commands: only `initadmin` and `create_dynamodb_tables` (under `src/core/management/commands/`).
- Cache backend `LocMemCache` is per-process and unsafe with `GUNICORN_WORKERS > 1` — the `core.E001` system check enforces this. For prod use Redis or Valkey.

## Frontend (`pages/`)
- Vue 3 Composition API, TypeScript. Component pattern: `.setup.ts` (logic) + `.vue` (template), each with a colocated `.spec.ts`.
- Features under `pages/src/features/`: `auth`, `barcode`, `dashboard`, `home`, `mobile-id`, `profile`. Each owns its own `api/`, components, and feature-local composables.
- Shared API (`pages/src/shared/api/`): `client.ts`, `axios.ts`, `csrf.ts` only. Per-feature API calls live alongside features — e.g. `features/auth/api/authApi.ts`, `features/auth/api/tokenRefresh.ts`.
- Composables (`pages/src/shared/composables/`): `api/{useLoading,useServerWakeup}`, `device/{useCameraPermission,useScannerDetection}`, `persistence/{useAutoSave}`. No barrel — import full paths.
- Path aliases (in `pages/path-aliases.json`): `@`, `@app`, `@auth`, `@barcode`, `@dashboard`, `@home`, `@mobile-id`, `@profile`, `@shared`. Use them; avoid deep relative paths.
- Auth: SPA POSTs `{ username, password }` plaintext over HTTPS to `/authn/login/`; backend issues JWT cookies. No client-side RSA or WebAuthn UI today.
- `yarn build` = `yarn typecheck && vite build`. `yarn format` (Prettier) and `yarn lint` (ESLint) before committing.
- Yarn 1.x only — locked via `packageManager` in `package.json`. Don't suggest npm or pnpm.

## Cross-stack conventions
- Use `localhost`, not `127.0.0.1`, for browser origins (CORS/CSRF config requires it).
- Coverage threshold: backend tests must hit `--fail-under=70` in CI.
- There is no `ops/` directory and no production-deploy GitHub workflow checked in — don't reference them.
