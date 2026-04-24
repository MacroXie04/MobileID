import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// ---- Mocks (hoisted before the module-under-test is imported) --------------
// `useUserInfo.js` calls `getUserInfo()` at module load time, so the mock
// factory runs before any top-level `const` is initialized. Use `vi.hoisted`
// to declare the mock fns in the same hoisted phase.

const {
  mockUserInfoApi,
  mockApiCallWithAutoRefresh,
  mockHasAuthTokens,
  mockGetUserInfoState,
  mockRefreshToken,
  mockHandleTokenExpired,
} = vi.hoisted(() => ({
  mockUserInfoApi: vi.fn(),
  mockApiCallWithAutoRefresh: vi.fn(),
  mockHasAuthTokens: vi.fn(),
  mockGetUserInfoState: vi.fn(),
  mockRefreshToken: vi.fn(),
  mockHandleTokenExpired: vi.fn(),
}));

vi.mock('@app/config/config', () => ({
  baseURL: 'http://localhost:8000',
}));

vi.mock('@shared/api/auth', () => ({
  userInfo: (...args) => mockUserInfoApi(...args),
}));

vi.mock('@shared/composables/api/useApi', () => ({
  useApi: () => ({
    apiCallWithAutoRefresh: mockApiCallWithAutoRefresh,
  }),
}));

vi.mock('@shared/utils/cookie', () => ({
  hasAuthTokens: () => mockHasAuthTokens(),
}));

vi.mock('@shared/state/authState', () => ({
  getUserInfo: () => mockGetUserInfoState(),
}));

vi.mock('@auth/composables/useToken', () => ({
  useToken: () => ({
    refreshToken: mockRefreshToken,
    handleTokenExpired: mockHandleTokenExpired,
  }),
}));

import { useUserInfo } from '@user/composables/useUserInfo';

// ---- Shared helpers --------------------------------------------------------

function makeFetchResponse({ ok = true, status = 200, blob } = {}) {
  return {
    ok,
    status,
    blob: vi.fn(async () => blob ?? new Blob(['avatar-bytes'])),
  };
}

describe('useUserInfo', () => {
  let originalFetch;
  let createdBlobUrls;
  let revokedBlobUrls;

  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock returns — individual tests override as needed.
    mockGetUserInfoState.mockReturnValue(null);
    mockHasAuthTokens.mockReturnValue(true);
    mockRefreshToken.mockResolvedValue(true);
    mockHandleTokenExpired.mockResolvedValue(undefined);

    // Track blob URL lifecycle — jsdom doesn't implement these.
    createdBlobUrls = [];
    revokedBlobUrls = [];
    let counter = 0;
    global.URL.createObjectURL = vi.fn(() => {
      counter += 1;
      const url = `blob:mock/${counter}`;
      createdBlobUrls.push(url);
      return url;
    });
    global.URL.revokeObjectURL = vi.fn((url) => {
      revokedBlobUrls.push(url);
    });

    originalFetch = global.fetch;
    global.fetch = vi.fn();

    // Reset the module-level state between tests (refs are shared across calls).
    useUserInfo().clearUserProfile();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    delete global.URL.createObjectURL;
    delete global.URL.revokeObjectURL;
  });

  describe('loadAvatar', () => {
    it('creates a blob URL when the fetch succeeds', async () => {
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));

      const { loadAvatar, avatarSrc } = useUserInfo();
      await loadAvatar();

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/authn/user_img/',
        expect.objectContaining({ method: 'GET', credentials: 'include' })
      );
      expect(avatarSrc.value).toBe('blob:mock/1');
      expect(createdBlobUrls).toHaveLength(1);
    });

    it('revokes the previous blob URL when a new one is created', async () => {
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));
      const { loadAvatar, avatarSrc } = useUserInfo();

      await loadAvatar();
      const first = avatarSrc.value;
      await loadAvatar();

      expect(revokedBlobUrls).toContain(first);
      expect(avatarSrc.value).not.toBe(first);
    });

    it('clears avatarSrc when the fetch returns non-ok', async () => {
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: false, status: 500 }));
      const { loadAvatar, avatarSrc } = useUserInfo();

      await loadAvatar();

      expect(avatarSrc.value).toBe('');
    });

    it('retries once after a successful token refresh on 401', async () => {
      global.fetch
        .mockResolvedValueOnce(makeFetchResponse({ ok: false, status: 401 }))
        .mockResolvedValueOnce(makeFetchResponse({ ok: true }));
      mockRefreshToken.mockResolvedValue(true);

      const { loadAvatar, avatarSrc } = useUserInfo();
      await loadAvatar();

      expect(mockRefreshToken).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(avatarSrc.value).toBe('blob:mock/1');
    });

    it('calls handleTokenExpired and clears avatar when refresh fails', async () => {
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: false, status: 401 }));
      mockRefreshToken.mockResolvedValue(false);

      const { loadAvatar, avatarSrc } = useUserInfo();
      await loadAvatar();

      expect(mockHandleTokenExpired).toHaveBeenCalledTimes(1);
      expect(avatarSrc.value).toBe('');
      // Only the first fetch should have happened — no retry.
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('clears avatar when fetch throws', async () => {
      global.fetch.mockRejectedValue(new Error('network down'));
      const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { loadAvatar, avatarSrc } = useUserInfo();
      await loadAvatar();

      expect(avatarSrc.value).toBe('');
      errorSpy.mockRestore();
    });
  });

  describe('loadUserProfile', () => {
    it('returns null when no auth tokens and not forced', async () => {
      mockHasAuthTokens.mockReturnValue(false);

      const { loadUserProfile } = useUserInfo();
      const result = await loadUserProfile();

      expect(result).toBeNull();
      expect(mockApiCallWithAutoRefresh).not.toHaveBeenCalled();
    });

    it('returns cached profile when present and not forced', async () => {
      mockGetUserInfoState.mockReturnValue({
        profile: { name: 'Cached', information_id: 'C-1' },
      });
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));

      const { loadUserProfile, profile } = useUserInfo();
      const result = await loadUserProfile();

      expect(result).toEqual({ name: 'Cached', information_id: 'C-1' });
      expect(profile.value).toEqual({ name: 'Cached', information_id: 'C-1' });
      expect(mockApiCallWithAutoRefresh).not.toHaveBeenCalled();
    });

    it('fetches fresh data when forceReload is true even with a cache hit', async () => {
      mockGetUserInfoState.mockReturnValue({
        profile: { name: 'Cached', information_id: 'C-1' },
      });
      mockApiCallWithAutoRefresh.mockResolvedValue({
        profile: { name: 'Fresh', information_id: 'F-1' },
      });
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));

      const { loadUserProfile, profile } = useUserInfo();
      const result = await loadUserProfile(true);

      expect(mockApiCallWithAutoRefresh).toHaveBeenCalledWith(
        'http://localhost:8000/authn/user_info/',
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual({ name: 'Fresh', information_id: 'F-1' });
      expect(profile.value).toEqual({ name: 'Fresh', information_id: 'F-1' });
    });

    it('fetches from API when there is no cache', async () => {
      mockApiCallWithAutoRefresh.mockResolvedValue({
        profile: { name: 'Fresh', information_id: 'F-1' },
      });
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));

      const { loadUserProfile, isLoaded } = useUserInfo();
      const result = await loadUserProfile();

      expect(result).toEqual({ name: 'Fresh', information_id: 'F-1' });
      expect(isLoaded.value).toBe(true);
    });

    it('returns null and leaves isLoaded=false when API response lacks a profile', async () => {
      mockApiCallWithAutoRefresh.mockResolvedValue({});
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));

      const { loadUserProfile, isLoaded } = useUserInfo();
      const result = await loadUserProfile();

      expect(result).toBeNull();
      expect(isLoaded.value).toBe(false);
    });

    it('propagates token errors unchanged', async () => {
      mockApiCallWithAutoRefresh.mockRejectedValue(new Error('Token expired'));
      const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { loadUserProfile } = useUserInfo();
      await expect(loadUserProfile()).rejects.toThrow('Token expired');

      errorSpy.mockRestore();
    });

    it('falls back to userInfo() API call for non-token errors', async () => {
      mockApiCallWithAutoRefresh.mockRejectedValue(new Error('network flakiness'));
      mockUserInfoApi.mockResolvedValue({
        profile: { name: 'Fallback', information_id: 'FB-1' },
      });
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));

      const { loadUserProfile } = useUserInfo();
      const result = await loadUserProfile();

      expect(mockUserInfoApi).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ name: 'Fallback', information_id: 'FB-1' });
    });

    it('resets isLoading flag after completion, even on success', async () => {
      mockApiCallWithAutoRefresh.mockResolvedValue({
        profile: { name: 'Fresh', information_id: 'F-1' },
      });
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));

      const { loadUserProfile, isLoading } = useUserInfo();
      await loadUserProfile();

      expect(isLoading.value).toBe(false);
    });
  });

  describe('clearUserProfile', () => {
    it('resets profile, isLoaded, isLoading, and revokes the blob URL', async () => {
      global.fetch.mockResolvedValue(makeFetchResponse({ ok: true }));
      mockApiCallWithAutoRefresh.mockResolvedValue({
        profile: { name: 'Fresh', information_id: 'F-1' },
      });

      const { loadUserProfile, clearUserProfile, profile, isLoaded, avatarSrc } = useUserInfo();
      await loadUserProfile();
      const createdUrl = avatarSrc.value;

      clearUserProfile();

      expect(profile.value).toEqual({ name: '', information_id: '' });
      expect(isLoaded.value).toBe(false);
      expect(avatarSrc.value).toBe('');
      expect(revokedBlobUrls).toContain(createdUrl);
    });
  });
});
