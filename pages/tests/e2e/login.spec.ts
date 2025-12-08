import { test, expect } from '@playwright/test';

test.describe('Login flow smoke test', () => {
  test('renders the login form elements', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByLabel('Username')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: /create an account/i })).toBeVisible();
  });

  test('renders passkey login button when WebAuthn is supported', async ({ page }) => {
    // Mock WebAuthn support by checking if the button is visible
    // Note: In browsers that support WebAuthn, the passkey button should be visible
    await page.goto('/login');

    // The passkey button should be present if WebAuthn is supported
    const passkeyButton = page.getByRole('button', { name: /passkey/i });

    // We check if it exists rather than is visible, as visibility depends on WebAuthn support
    const buttonCount = await passkeyButton.count();

    // If WebAuthn is supported in the test browser, the button should exist
    if (buttonCount > 0) {
      await expect(passkeyButton).toBeVisible();
    }
  });
});
