import { defineConfig } from '@playwright/test';
import base from './playwright.config';

const PORT = Number(process.env.E2E_PREVIEW_PORT ?? 4175);
const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  ...base,
  testMatch: [
    'tests/e2e/login.spec.ts',
    'tests/e2e/auth-redirects.spec.ts',
    'tests/e2e/dashboard.spec.ts',
  ],
  use: { ...base.use, baseURL: BASE_URL },
  webServer: {
    command: `VITE_API_BASE_URL=/ npm run build && npm run preview -- --host 127.0.0.1 --port ${PORT} --strictPort`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
    timeout: 180 * 1000,
  },
});
