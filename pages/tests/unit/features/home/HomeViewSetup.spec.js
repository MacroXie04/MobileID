import { beforeEach, describe, expect, it, vi } from 'vitest';

// Mock Vue lifecycle hooks
const mountedCallbacks = [];
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue');
  return {
    ...actual,
    onMounted: (cb) => mountedCallbacks.push(cb),
  };
});

const mockGetUserInfo = vi.fn();
const mockGetApiError = vi.fn();
vi.mock('@shared/state/authState', () => ({
  getUserInfo: () => mockGetUserInfo(),
  getApiError: () => mockGetApiError(),
}));

// Mock the HomeSchoolView import to avoid deep dependency resolution
vi.mock('@home/views/HomeSchoolView.vue', () => ({
  default: { name: 'HomeSchoolView', template: '<div />' },
}));

// Mock the CSS import
vi.mock('@/assets/styles/home/home-merged.css', () => ({}));

import { useHomeViewSetup } from '@home/views/HomeView.setup';

describe('useHomeViewSetup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mountedCallbacks.length = 0;
  });

  function setupAndMount() {
    const result = useHomeViewSetup();
    // Execute onMounted callbacks
    mountedCallbacks.forEach((cb) => cb());
    return result;
  }

  it('should start in loading state', () => {
    const { loading } = useHomeViewSetup();
    expect(loading.value).toBe(true);
  });

  it('should show home view when user info exists', () => {
    mockGetApiError.mockReturnValue(null);
    mockGetUserInfo.mockReturnValue({ id: 1, username: 'test' });

    const { loading, apiError } = setupAndMount();

    expect(loading.value).toBe(false);
    expect(apiError.value).toBeNull();
  });

  it('should set API error when connection failed', () => {
    const error = 'Connection refused';
    mockGetApiError.mockReturnValue(error);

    const { loading, apiError } = setupAndMount();

    expect(loading.value).toBe(false);
    expect(apiError.value).toBe('Connection refused');
  });

  it('should set error when user info is missing and no API error', () => {
    mockGetApiError.mockReturnValue(null);
    mockGetUserInfo.mockReturnValue(null);

    const { loading, apiError } = setupAndMount();

    expect(loading.value).toBe(false);
    expect(apiError.value).toBe('Unable to load user data');
  });

  it('should not check user info when API error exists', () => {
    mockGetApiError.mockReturnValue('Server down');

    setupAndMount();

    expect(mockGetUserInfo).not.toHaveBeenCalled();
  });

  describe('retryConnection', () => {
    it('should reload the page', () => {
      const reloadMock = vi.fn();
      Object.defineProperty(window, 'location', {
        value: { reload: reloadMock },
        writable: true,
      });

      const { retryConnection } = useHomeViewSetup();
      retryConnection();

      expect(reloadMock).toHaveBeenCalled();
    });
  });
});
