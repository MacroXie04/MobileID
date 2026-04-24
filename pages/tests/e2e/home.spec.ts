import { test, expect } from '@playwright/test';
import { mockAuthenticated, mockBarcodeEndpoints } from './helpers';

test.skip(
  ({ browserName }) => browserName !== 'chromium',
  'Home renders scanner / TensorFlow-backed child components; Chromium is the canonical target.'
);

test.describe('Home page for activated users', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticated(page);
    await mockBarcodeEndpoints(page);
  });

  test('activated user reaches home success state', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByText('Connection Error')).toHaveCount(0);
    await expect(page.getByText('Loading...')).toHaveCount(0, { timeout: 10_000 });
  });
});
