import type { Page } from '@playwright/test';

export type MockUser = {
  username?: string;
  is_activated: boolean;
  profile?: Record<string, unknown> | null;
  user_type?: string;
};

const DEFAULT_USER: Required<MockUser> = {
  username: 'testuser',
  is_activated: true,
  user_type: 'standard',
  profile: { full_name: 'Test User', student_id: 'T0001' },
};

const PNG_1X1 = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNgAAIAAAUAAen63NgAAAAASUVORK5CYII=',
  'base64'
);

const jsonResponse = (status: number, body: unknown) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

export async function mockHealth(page: Page): Promise<void> {
  await page.route('**/health/', async (route) =>
    route.fulfill(jsonResponse(200, { status: 'healthy', service: 'MobileID' }))
  );
}

export async function mockCsrf(page: Page): Promise<void> {
  await page.route('**/authn/csrf/', async (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: { 'set-cookie': 'csrftoken=test-csrf; Path=/; SameSite=Lax' },
      body: JSON.stringify({ csrfToken: 'test-csrf' }),
    })
  );
}

export async function mockUnauthenticated(page: Page): Promise<void> {
  await mockHealth(page);
  await mockCsrf(page);
  await page.route('**/authn/user_info/', async (route) =>
    route.fulfill(jsonResponse(401, { detail: 'Authentication credentials were not provided.' }))
  );
  await page.route('**/authn/token/refresh/', async (route) =>
    route.fulfill(jsonResponse(401, { detail: 'Token invalid' }))
  );
}

export async function mockAuthenticated(page: Page, user: Partial<MockUser> = {}): Promise<void> {
  const merged = { ...DEFAULT_USER, ...user };
  await mockHealth(page);
  await mockCsrf(page);
  await page.route('**/authn/user_info/', async (route) =>
    route.fulfill(jsonResponse(200, merged))
  );
  await page.route('**/authn/token/refresh/', async (route) =>
    route.fulfill(jsonResponse(200, { detail: 'ok' }))
  );
  await page.route('**/authn/user_img/', async (route) =>
    route.fulfill({ status: 200, contentType: 'image/png', body: PNG_1X1 })
  );
}

export async function mockBarcodeEndpoints(page: Page): Promise<void> {
  await page.route('**/active_profile/', async (route) =>
    route.fulfill(jsonResponse(200, { profile_id: 'p1', name: 'Test Profile' }))
  );
  await page.route('**/barcode_dashboard/', async (route) =>
    route.fulfill(
      jsonResponse(200, {
        settings: {},
        pullSettings: {},
        barcodes: [],
        barcodeChoices: [],
      })
    )
  );
  await page.route('**/generate_barcode/', async (route) =>
    route.fulfill(jsonResponse(200, { barcode: 'data:image/png;base64,' }))
  );
}
