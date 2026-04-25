import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const mountedCallbacks = [];
const mockInitializeHome = vi.fn(async () => {});

vi.mock('vue', async () => {
  const actual = await vi.importActual('vue');
  return {
    ...actual,
    onMounted: (cb) => mountedCallbacks.push(cb),
  };
});

const mockGetUserInfo = vi.fn();
const mockGetApiError = vi.fn();

vi.mock('@auth', () => ({
  getUserInfo: () => mockGetUserInfo(),
  getApiError: () => mockGetApiError(),
}));

vi.mock('@home/composables/useHomeLogic', () => ({
  useHomeLogic: () => ({
    profile: ref({ name: 'Test User', information_id: 'A123' }),
    avatarSrc: ref(''),
    loading: ref(false),
    serverStatus: ref('Emergency'),
    barcodeDisplayRef: ref(null),
    isRefreshingToken: ref(false),
    scannerDetectionEnabled: ref(false),
    preferFrontCamera: ref(true),
    handleGenerate: vi.fn(),
    initializeHome: mockInitializeHome,
  }),
}));

vi.mock('@mobile-id/components/header/Header.vue', () => ({
  default: { name: 'Header', template: '<div />' },
}));
vi.mock('@mobile-id/components/user-profile/UserProfile.vue', () => ({
  default: { name: 'UserProfile', template: '<div />' },
}));
vi.mock('@mobile-id/components/barcode-display/BarcodeDisplay.vue', () => ({
  default: { name: 'BarcodeDisplay', template: '<div />' },
}));
vi.mock('@mobile-id/components/grid-menu/GridMenu.vue', () => ({
  default: { name: 'GridMenu', template: '<div />' },
}));
vi.mock('@home/styles/HomeShell.css', () => ({}));
vi.mock('@home/styles/Home.css', () => ({}));

import { useHomeViewSetup } from '@home/views/HomeView.setup';

describe('useHomeViewSetup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mountedCallbacks.length = 0;
  });

  async function setupAndMount() {
    const result = useHomeViewSetup();
    for (const cb of mountedCallbacks) {
      await cb();
    }
    return result;
  }

  it('starts in page loading state', () => {
    const { pageLoading } = useHomeViewSetup();
    expect(pageLoading.value).toBe(true);
  });

  it('initializes the single home when user info exists', async () => {
    mockGetApiError.mockReturnValue(null);
    mockGetUserInfo.mockReturnValue({ id: 1, username: 'test' });

    const { pageLoading, apiError } = await setupAndMount();

    expect(mockInitializeHome).toHaveBeenCalledTimes(1);
    expect(pageLoading.value).toBe(false);
    expect(apiError.value).toBeNull();
  });

  it('sets the API error when connection failed', async () => {
    mockGetApiError.mockReturnValue('Connection refused');

    const { pageLoading, apiError } = await setupAndMount();

    expect(pageLoading.value).toBe(false);
    expect(apiError.value).toBe('Connection refused');
    expect(mockInitializeHome).not.toHaveBeenCalled();
  });

  it('sets an error when user info is missing and no API error exists', async () => {
    mockGetApiError.mockReturnValue(null);
    mockGetUserInfo.mockReturnValue(null);

    const { pageLoading, apiError } = await setupAndMount();

    expect(pageLoading.value).toBe(false);
    expect(apiError.value).toBe('Unable to load user data');
    expect(mockInitializeHome).not.toHaveBeenCalled();
  });

  it('does not check user info when API error exists', async () => {
    mockGetApiError.mockReturnValue('Server down');

    await setupAndMount();

    expect(mockGetUserInfo).not.toHaveBeenCalled();
  });

  it('reloads the page when retryConnection is called', () => {
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
