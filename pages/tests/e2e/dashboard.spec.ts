import { test, expect } from '@playwright/test';
import { mockAuthenticated, mockBarcodeEndpoints } from './helpers';

test.describe('Dashboard for activated users', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticated(page);
    await mockBarcodeEndpoints(page);
  });

  test('activated user reaches /dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByRole('heading', { name: 'MobileID Dashboard', level: 3 })).toBeVisible();
    await expect(page.getByRole('button', { name: /back to home/i })).toBeVisible();
  });

  test('activated user visiting /pending bounces to /', async ({ page }) => {
    await page.goto('/pending');
    await page.waitForURL((url) => url.pathname === '/');
    await expect(page).toHaveURL(/\/$/);
  });

  test('deep-linking ?tab=Devices opens the Devices pane', async ({ page }) => {
    await page.goto('/dashboard?tab=Devices');
    await expect(page.getByRole('heading', { name: 'Logged-in Devices' })).toBeVisible();
    await expect(page).toHaveURL(/[?&]tab=Devices/);
  });

  test('selecting a nav item updates the ?tab= query param', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: 'MobileID Dashboard', level: 3 })).toBeVisible();
    // Desktop viewport (1280x720) shows the navigation rail buttons.
    await page.getByRole('button', { name: 'Available Barcodes' }).click();
    await page.waitForURL(/[?&]tab=Barcodes/);
    await expect(page.getByRole('heading', { name: 'Available Barcodes' })).toBeVisible();
  });
});
