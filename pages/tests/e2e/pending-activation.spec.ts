import { test, expect } from '@playwright/test';
import { mockAuthenticated } from './helpers';

test.describe('Pending activation gating', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticated(page, { is_activated: false });
  });

  test('inactive user visiting /dashboard lands on /pending', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL('**/pending');
    await expect(
      page.getByRole('heading', { name: 'Access Denied' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Sign Out', exact: true })
    ).toBeVisible();
  });

  test('inactive user visiting / lands on /pending', async ({ page }) => {
    await page.goto('/');
    await page.waitForURL('**/pending');
    await expect(
      page.getByRole('heading', { name: 'Access Denied' })
    ).toBeVisible();
  });
});
