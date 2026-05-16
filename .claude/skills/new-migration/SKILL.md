---
name: new-migration
description: Create a new Django migration for MobileID safely. Use when models change, the user mentions makemigrations, or a model edit is on the table.
---

Migration discipline for MobileID — CI's `migration-file-guard` will reject any PR that modifies an existing migration file. Always add a new migration on top.

## Procedure

1. From `src/`, generate the migration:
   ```bash
   python manage.py makemigrations <app>
   ```
2. **Verify it's a NEW file** in `src/<app>/migrations/`. If `git status` shows a *modified* migration instead of a new one, stop — something is wrong (likely you reverted a generated file or someone else's migration is in your tree).
3. Apply locally:
   ```bash
   python manage.py migrate
   ```
4. Confirm model state and migrations are in sync (this is what CI's `migration-check` job runs):
   ```bash
   python manage.py makemigrations --check
   ```
5. Commit the new migration **alongside** the model change.

## If you're tempted to edit an existing migration

Don't. Either:
- Generate a new migration that supersedes the prior one (e.g., a follow-up `AlterField`), or
- Revert the model change and rethink the schema.

The `.claude/hooks/migration-guard.sh` PreToolUse hook will refuse Edit/Write calls against tracked migration files for exactly this reason.
