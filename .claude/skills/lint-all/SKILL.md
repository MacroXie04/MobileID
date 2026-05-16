---
name: lint-all
description: Run all MobileID linters and typecheckers (backend + frontend) and report what failed. Use before committing or when the user asks to check code style.
---

Run every check CI runs, in order. Report pass/fail per command.

## Backend — from `src/`

```bash
black --check .         # formatting (line length 88). Drop --check to auto-fix.
ruff check .            # linting
flake8 .                # style
```

CI runs all three in the `backend-lint` job; each is a hard gate.

## Frontend — from `pages/`

```bash
yarn prettier --check .     # how CI runs it
yarn lint                   # ESLint on src/
yarn typecheck              # vue-tsc across tsconfig.app.json, tsconfig.test.json, tsconfig.node.json
```

Use `yarn format` to auto-fix Prettier formatting issues.

## Behavior

- Run them sequentially and report which failed; don't stop on first failure unless the user asked for fail-fast.
- Do not auto-fix unless the user explicitly asked to format/fix.
