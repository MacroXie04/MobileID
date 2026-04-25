import { beforeEach, describe, expect, it, vi } from 'vitest';

// Mocks for router dependencies — declared at module scope so that they
// are hoisted above the router import.
const {
  mockGetUserInfo,
  mockIsUserInfoStale,
  mockRefreshToken,
  mockSetApiError,
  mockSetUserInfo,
  mockUserInfo,
} = vi.hoisted(() => ({
  mockGetUserInfo: vi.fn(),
  mockIsUserInfoStale: vi.fn(),
  mockRefreshToken: vi.fn(),
  mockSetApiError: vi.fn(),
  mockSetUserInfo: vi.fn(),
  mockUserInfo: vi.fn(),
}));
vi.mock('@auth', () => ({
  userInfo: (...args: unknown[]) => mockUserInfo(...args),
  refreshToken: (...args: unknown[]) => mockRefreshToken(...args),
  getUserInfo: () => mockGetUserInfo(),
  setUserInfo: (info: unknown) => mockSetUserInfo(info),
  isUserInfoStale: () => mockIsUserInfoStale(),
  setApiError: (msg: unknown) => mockSetApiError(msg),
}));

// All lazy-loaded views resolve to an empty component stub so dynamic imports
// succeed without touching real views.
vi.mock('@auth/views/login/LoginView.vue', () => ({ default: {} }));
vi.mock('@auth/views/register/RegisterView.vue', () => ({ default: {} }));
vi.mock('@auth/views/privacy/PrivacyView.vue', () => ({ default: {} }));
vi.mock('@auth/views/pending/PendingActivationView.vue', () => ({ default: {} }));
vi.mock('@home/views/HomeView.vue', () => ({ default: {} }));
vi.mock('@dashboard/views/MobileIDDashboardView.vue', () => ({ default: {} }));

// Capture the guard the router registers so we can drive it directly.
let registeredGuard = null;
vi.mock('vue-router', () => ({
  createRouter: ({ routes }) => ({
    routes,
    beforeEach(fn) {
      registeredGuard = fn;
    },
  }),
  createWebHistory: () => ({}),
}));

async function loadRouter() {
  registeredGuard = null;
  vi.resetModules();
  await import('@app/router/index');
  return registeredGuard;
}

function makeTo(overrides = {}) {
  return {
    fullPath: '/home',
    name: 'home',
    meta: { requiresAuth: true, requiresActivation: true },
    ...overrides,
  };
}

describe('router beforeEach guard', () => {
  let guard;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockGetUserInfo.mockReturnValue(null);
    mockIsUserInfoStale.mockReturnValue(false);
    guard = await loadRouter();
  });

  it('allows public routes through without fetching user info', async () => {
    const next = vi.fn();

    await guard(makeTo({ meta: { feature: 'auth' } }), {}, next);

    expect(mockUserInfo).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalledWith();
  });

  it('uses cached user info when present and fresh', async () => {
    mockGetUserInfo.mockReturnValue({ is_activated: true });
    const next = vi.fn();

    await guard(makeTo(), {}, next);

    expect(mockUserInfo).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalledWith();
  });

  it('fetches fresh user info when cache is stale', async () => {
    mockGetUserInfo.mockReturnValue({ is_activated: true });
    mockIsUserInfoStale.mockReturnValue(true);
    mockUserInfo.mockResolvedValue({ is_activated: true, username: 'alice' });
    const next = vi.fn();

    await guard(makeTo(), {}, next);

    expect(mockUserInfo).toHaveBeenCalledTimes(1);
    expect(mockSetUserInfo).toHaveBeenCalledWith({
      is_activated: true,
      username: 'alice',
    });
    expect(next).toHaveBeenCalledWith();
  });

  it('falls back to refresh when userInfo fetch returns null', async () => {
    mockUserInfo.mockResolvedValueOnce(null).mockResolvedValueOnce({ is_activated: true });
    mockRefreshToken.mockResolvedValue(true);
    const next = vi.fn();

    await guard(makeTo(), {}, next);

    expect(mockRefreshToken).toHaveBeenCalledTimes(1);
    expect(mockUserInfo).toHaveBeenCalledTimes(2);
    expect(mockSetUserInfo).toHaveBeenCalledWith({ is_activated: true });
    expect(next).toHaveBeenCalledWith();
  });

  it('redirects to /login when refresh also fails', async () => {
    mockUserInfo.mockResolvedValue(null);
    mockRefreshToken.mockResolvedValue(false);
    const to = makeTo({ fullPath: '/dashboard' });
    const next = vi.fn();

    await guard(to, {}, next);

    expect(next).toHaveBeenCalledWith({
      path: '/login',
      query: { redirect: '/dashboard' },
    });
  });

  it('redirects non-activated users to pending page for activation-required routes', async () => {
    mockUserInfo.mockResolvedValue({ is_activated: false });
    const next = vi.fn();

    await guard(makeTo(), {}, next);

    expect(next).toHaveBeenCalledWith({ name: 'pending-activation' });
  });

  it('does not redirect non-activated users on routes without requiresActivation', async () => {
    mockUserInfo.mockResolvedValue({ is_activated: false });
    const next = vi.fn();

    await guard(
      makeTo({
        name: 'pending-activation',
        meta: { requiresAuth: true, feature: 'auth' },
        fullPath: '/pending',
      }),
      {},
      next
    );

    expect(next).toHaveBeenCalledWith();
  });

  it('redirects activated users away from the pending page', async () => {
    mockUserInfo.mockResolvedValue({ is_activated: true });
    const next = vi.fn();

    await guard(
      makeTo({
        name: 'pending-activation',
        meta: { requiresAuth: true, feature: 'auth' },
        fullPath: '/pending',
      }),
      {},
      next
    );

    expect(next).toHaveBeenCalledWith({ path: '/' });
  });

  it('reports API offline and passes through when guard throws', async () => {
    mockUserInfo.mockRejectedValue(new Error('network down'));
    const next = vi.fn();

    await guard(makeTo(), {}, next);

    expect(mockSetApiError).toHaveBeenCalledWith('API server is offline');
    expect(next).toHaveBeenCalledWith();
  });

  it('does not persist userInfo when fetch returns falsy after refresh', async () => {
    mockUserInfo.mockResolvedValueOnce(null).mockResolvedValueOnce(null);
    mockRefreshToken.mockResolvedValue(true);
    const next = vi.fn();

    await guard(makeTo(), {}, next);

    expect(mockSetUserInfo).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalledWith({
      path: '/login',
      query: { redirect: '/home' },
    });
  });
});

describe('router route table', () => {
  it('includes expected named routes', async () => {
    // The route array is defined at module load time; re-import to inspect it.
    vi.resetModules();
    // The `createRouter` mock captures the routes option; import again and
    // read via the side-effect of registering a guard.
    let capturedRoutes = null;
    vi.doMock('vue-router', () => ({
      createRouter: ({ routes }) => {
        capturedRoutes = routes;
        return { beforeEach: () => {} };
      },
      createWebHistory: () => ({}),
    }));

    await import('@app/router/index');

    const names = capturedRoutes.filter((r) => r.name).map((r) => r.name);
    expect(names).toEqual(
      expect.arrayContaining([
        'auth-login',
        'auth-register',
        'privacy',
        'pending-activation',
        'home',
        'dashboard',
      ])
    );

    const catchAll = capturedRoutes.find((r) => r.path === '/:pathMatch(.*)*');
    expect(catchAll).toBeTruthy();
    expect(catchAll.redirect()).toEqual({ path: '/' });
  });
});
