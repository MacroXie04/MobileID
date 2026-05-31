// The ONE place in the app where `console.*` is permitted. Every other module must
// route through this logger; eslint bans `console` everywhere except this file
// (see the dedicated override in eslint.config.js).
//
// Levels:
//   debug/info  -> "noisy" developer trace. Emitted only in real dev mode; silent
//                  under Vitest (MODE === 'test') and production builds.
//   warn/error  -> always pass through, in every mode, so real problems still
//                  surface in production telemetry / breadcrumbs.
//
// Env detection mirrors existing repo conventions: config.ts reads
// `import.meta.env.PROD`, useAuthenticatedRequest.ts reads `import.meta.env?.MODE`.
// Vitest sets `import.meta.env.MODE === 'test'` and `import.meta.env.DEV === false`,
// so gating the noisy levels on `DEV` keeps them silent under unit tests.
//
// `no-console` is disabled for this file via eslint.config.js — this is the one
// module permitted to call console directly.

const env = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env : undefined;

// True only for `vite dev` / non-production runs in dev mode. False under
// `vite build` (PROD) and under Vitest (MODE === 'test', DEV === false).
const noisyEnabled = Boolean(env?.DEV) && env?.MODE !== 'test';

type LogArgs = unknown[];

export const logger = {
  debug: (...args: LogArgs): void => {
    if (noisyEnabled) console.debug(...args);
  },
  info: (...args: LogArgs): void => {
    if (noisyEnabled) console.info(...args);
  },
  warn: (...args: LogArgs): void => {
    console.warn(...args);
  },
  error: (...args: LogArgs): void => {
    console.error(...args);
  },
};

export default logger;
