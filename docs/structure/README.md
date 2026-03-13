# Repository Structure

```
MobileID/
├── src/                    # Django backend
│   ├── authn/              # Authentication app (JWT, WebAuthn, RSA)
│   ├── index/              # Barcode management app
│   ├── core/               # Django config, middleware, settings
│   └── pyproject.toml      # Python dependencies (managed by uv)
├── pages/                  # Vue.js frontend
│   ├── src/
│   │   ├── app/            # Entry point, router, config
│   │   ├── features/       # Feature modules (auth, home, dashboard, user, school)
│   │   └── shared/         # Reusable components, composables, API layer
│   └── tests/              # Frontend tests (Vitest + Playwright)
├── infra/                  # Infrastructure and operations
│   ├── aws/                # AWS provisioning and operations scripts
│   └── db/exports/         # Database export files
├── docs/                   # Documentation
│   ├── architecture/       # System architecture
│   ├── development/        # Dev setup and workflow
│   ├── operations/         # Deployment and operations
│   └── structure/          # This file
├── scripts/                # Compatibility wrappers (delegate to infra/)
└── .github/workflows/      # CI/CD pipelines
```
