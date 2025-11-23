# Pages Frontend Structure

This document captures the domain boundaries, directory layout, and alias strategy for the `pages/` frontend so future contributors can quickly orient themselves.

## Feature Domains
- **Auth** – login, registration, passkeys, and token lifecycle helpers.
- **Dashboard** – barcode dashboard UI, settings cards, scanners, and barcode utilities.
- **User** – end-user profile display/edit flows, barcode renderers, and profile utilities.
- **School** – school dashboard widgets and supporting composables.
- **Home** – entry experiences for anonymous, user, and school personas.
- **Shared** – reusable API clients, composables, utilities, and UI primitives.

## Directory Layout
```
src/
  assets/
    images/{home,school,shared,user}
    styles/{auth,dashboard,home,school,shared,user}
  features/
    auth/
    dashboard/
    home/
    school/
    user/
  shared/
    api/
    components/
    composables/
    utils/
  views/        # Thin wrappers that lazy-load feature views
```
Each feature folder co-locates its components, composables, utilities, and views plus an `index.js` that re-exports the feature’s public API surface.

## Path Aliases
Aliases are defined in `path-aliases.json` and consumed by Vite, Vitest, and ESLint:
```
@        -> ./src
@auth    -> ./src/features/auth
@dashboard -> ./src/features/dashboard
@home    -> ./src/features/home
@school  -> ./src/features/school
@user    -> ./src/features/user
@shared  -> ./src/shared
```
Import from the shortest alias possible (e.g., `import { useUserInfo } from '@user/composables/useUserInfo.js'`) to avoid fragile relative paths.

## Migration Notes
- Legacy `components/*`, `composables/*`, `utils/*`, and feature views have been migrated into `src/features/*`.
- Route-level files in `src/views` now act as compatibility wrappers that simply load the corresponding feature view component.
- Global CSS variables live in `src/assets/styles/shared/tokens.css`; feature-specific styles now reside under `src/assets/styles/<feature>/`.
- Shared API helpers moved to `src/shared/api`, and common utilities/composables moved to `src/shared/{utils,composables}`.

Refer to this file whenever adding a new feature module or alias.
# Frontend Structure & Feature Boundaries

This document defines the desired module layout for the `@pages` frontend so that subsequent refactors have a single source of truth.

## Feature Domains
- **Auth** – login, registration, passkey, and token refresh flows (currently `views/authn`, `composables/auth`, `api/auth.js`, `utils/auth`).
- **Dashboard** – barcode inventory management, settings, and dashboard cards (`components/dashboard`, `composables/dashboard`, `composables/barcode`).
- **User** – profile viewing/editing, image cropper, and barcode rendering for end-users (`components/user`, `composables/user`, `utils/user`).
- **School** – school-facing dashboard widgets (`components/school`, `composables/school`, `views/home/HomeSchool.vue`).
- **Home** – landing experiences for anonymous/authenticated contexts (`views/home`, `composables/home`).
- **Shared** – cross-cutting helpers, networking, and styling (common composables, API clients, assets, reusable UI).

## Target Directory Layout
```
src/
  features/
    auth/
    dashboard/
    home/
    school/
    user/
  shared/
    api/
    components/
    composables/
    utils/
  router/
  App.vue
  main.js
```
Each feature folder groups its components, composables, and feature-scoped utilities (e.g., `src/features/user/components/UserProfile.vue`). Shared functionality is colocated under `src/shared` with clear boundaries.

## Conventions
- **Public surface** – every feature exposes an `index.js` (or `.ts`) re-exporting components/composables that other modules may consume; intra-feature imports stay relative.
- **Aliasing** – configure Vite/ESLint/Vitest aliases such as `@auth`, `@dashboard`, `@user`, and `@shared` to avoid brittle relative paths.
- **Styling** – prefer scoped `<style>` blocks per component; when global tokens are required, store them in `src/assets/styles` and import via the shared alias.
- **Testing** – colocate unit tests next to the feature artifacts they validate (e.g., `src/features/user/components/__tests__`).

## Migration Notes
- Existing folders (`components/*`, `composables/*`, `utils/*`, `views/*`) will be migrated into their corresponding feature or shared directories without altering business logic.
- Route definitions in `src/router/index.js` will consume the feature entry components (lazy-loaded) after files move.
- Asset paths will be updated to reflect the new `src/assets/images/<feature>` convention.

This plan acts as the checklist for the remaining refactor steps (folder moves, routing updates, asset consolidation, and documentation updates).

