import { test, expect } from '@playwright/test';
import { mockUnauthenticated } from './helpers';

test.describe('Auth guard redirects', () => {
  test.beforeEach(async ({ page }) => {
    await mockUnauthenticated(page);
  });

  test('unauthenticated /dashboard is redirected to /login', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL((url) => url.pathname === '/login');
    await expect(page.getByRole('button', { name: 'Sign In', exact: true })).toBeVisible();
  });

  test('unknown route falls through / catch-all to /login', async ({ page }) => {
    await page.goto('/does-not-exist');
    await page.waitForURL((url) => url.pathname === '/login');
    await expect(page.getByLabel('Username')).toBeVisible();
  });
});
