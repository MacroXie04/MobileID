import { test, expect } from '@playwright/test';
import { mockUnauthenticated } from './helpers';

test.describe('Register page', () => {
  test.beforeEach(async ({ page }) => {
    await mockUnauthenticated(page);
  });

  test('renders the register form elements', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByLabel('Username')).toBeVisible();
    await expect(page.getByLabel('Full Name')).toBeVisible();
    await expect(page.getByLabel('Password', { exact: true })).toBeVisible();
    await expect(page.getByLabel('Confirm Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Account', exact: true })).toBeVisible();
  });

  test('"Sign in instead" link navigates to /login', async ({ page }) => {
    await page.goto('/register');
    await page.getByRole('link', { name: /sign in instead/i }).click();
    await page.waitForURL('**/login');
    await expect(page.getByRole('button', { name: 'Sign In', exact: true })).toBeVisible();
  });
});
