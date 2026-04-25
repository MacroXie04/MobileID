import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import HomeView from '@home/views/HomeView.vue';

const useHomeViewSetupMock = vi.fn();

vi.mock('@home/views/HomeView.setup', () => ({
  Header: { name: 'Header', template: '<div data-test="header" />' },
  UserProfile: { name: 'UserProfile', template: '<div data-test="profile" />' },
  BarcodeDisplay: { name: 'BarcodeDisplay', template: '<div data-test="barcode" />' },
  GridMenu: { name: 'GridMenu', template: '<div data-test="grid-menu" />' },
  useHomeViewSetup: () => useHomeViewSetupMock(),
}));

describe('HomeView', () => {
  it('renders the single home content when loading is complete and there is no API error', () => {
    useHomeViewSetupMock.mockReturnValue({
      pageLoading: false,
      apiError: null,
      retryConnection: vi.fn(),
      profile: { name: 'Test User', information_id: 'A123' },
      avatarSrc: '',
      homeLoading: false,
      serverStatus: 'Emergency',
      barcodeDisplayRef: ref(null),
      isRefreshingToken: false,
      scannerDetectionEnabled: false,
      preferFrontCamera: true,
      handleGenerate: vi.fn(),
      isDetectionActive: false,
      isBarcodeVisible: false,
      scannerDetected: false,
    });

    const wrapper = mount(HomeView);

    expect(wrapper.find('[data-test="header"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="profile"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="barcode"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="grid-menu"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain('Connection Error');
  });

  it('renders the error page when the API error is present', () => {
    useHomeViewSetupMock.mockReturnValue({
      pageLoading: false,
      apiError: 'Server unavailable',
      retryConnection: vi.fn(),
      profile: null,
      avatarSrc: '',
      homeLoading: false,
      serverStatus: 'Emergency',
      barcodeDisplayRef: ref(null),
      isRefreshingToken: false,
      scannerDetectionEnabled: false,
      preferFrontCamera: true,
      handleGenerate: vi.fn(),
      isDetectionActive: false,
      isBarcodeVisible: false,
      scannerDetected: false,
    });

    const wrapper = mount(HomeView);

    expect(wrapper.text()).toContain('Connection Error');
    expect(wrapper.text()).toContain('Server unavailable');
  });
});
