---
name: run-tests
description: Run MobileID backend and/or frontend tests. Use when the user asks to run tests, check coverage, or verify changes locally.
---

Run the appropriate test suite(s) for the changes at hand. If unclear which side changed, infer from `git status` (or run both).

## Backend — from `src/`

```bash
python manage.py test -v 2                                                       # all tests
python manage.py test authn -v 2                                                 # one app
python manage.py test authn.tests.test_auth_api.AuthenticationAPITest -v 2       # one class
python manage.py test authn.tests.test_auth_api.AuthenticationAPITest.test_login_success -v 2
```

CI uses `DJANGO_SETTINGS_MODULE=core.settings.dev` and enforces coverage `--fail-under=70`:

```bash
coverage run manage.py test -v 2
coverage report --fail-under=70
```

## Frontend — from `pages/`

```bash
yarn test:unit              # Vitest, single run (CI mode)
yarn test                   # Vitest watch mode
yarn test:e2e               # Playwright (one-time setup: npx playwright install --with-deps)
yarn test:e2e:ci            # list reporter
yarn test:e2e:preview       # against `vite preview` (playwright.preview.config.ts)
```

Report failures concisely. Don't auto-fix — the user decides what to do with failures.
