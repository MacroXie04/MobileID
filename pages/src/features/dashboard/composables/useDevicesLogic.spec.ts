import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, nextTick } from 'vue';
import { mount } from '@vue/test-utils';

// Mock @auth so useAuthenticatedRequest returns our controllable apiCall mock.
const { mockApiCall } = vi.hoisted(() => ({
  mockApiCall: vi.fn(),
}));
vi.mock('@auth', () => ({
  useAuthenticatedRequest: () => ({
    apiCallWithAutoRefresh: mockApiCall,
  }),
}));

// Import after mocks are registered.
import { useDevicesLogic } from '@dashboard/composables/useDevicesLogic';

/**
 * Mount a tiny harness so onMounted fires and we can read the composable result
 * off the component instance.
 */
function mountLogic() {
  let logic;
  const Harness = defineComponent({
    setup() {
      logic = useDevicesLogic();
      return () => null;
    },
  });
  const wrapper = mount(Harness);
  return { wrapper, logic };
}

const sampleDevices = [
  {
    id: 1,
    is_current: true,
    device_type: 'mobile',
    device_name: 'A',
    created_at: '2026-01-01T00:00:00Z',
    expires_at: '2026-12-31T00:00:00Z',
  },
  {
    id: 2,
    is_current: false,
    device_type: 'desktop',
    device_name: 'B',
    created_at: '2026-01-02T00:00:00Z',
    expires_at: '2026-12-31T00:00:00Z',
  },
];

describe('useDevicesLogic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('fetchDevices via onMounted', () => {
    it('fetches devices with GET /authn/devices/ on mount and populates devices', async () => {
      mockApiCall.mockResolvedValue({ devices: sampleDevices });

      const { logic } = mountLogic();
      // Allow the onMounted async fetch to settle.
      await nextTick();
      await nextTick();

      expect(mockApiCall).toHaveBeenCalledWith('/authn/devices/', { method: 'GET' });
      expect(logic.devices.value).toEqual(sampleDevices);
      expect(logic.loading.value).toBe(false);
      expect(logic.error.value).toBeNull();
    });

    it('defaults devices to [] when response object has no devices array', async () => {
      mockApiCall.mockResolvedValue({ count: 0 });

      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      expect(logic.devices.value).toEqual([]);
      expect(logic.error.value).toBeNull();
    });

    it('defaults devices to [] when response is null', async () => {
      mockApiCall.mockResolvedValue(null);

      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      expect(logic.devices.value).toEqual([]);
    });

    it('defaults devices to [] when response is undefined', async () => {
      mockApiCall.mockResolvedValue(undefined);

      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      expect(logic.devices.value).toEqual([]);
    });

    it('sets error from err.message and clears devices when the request throws', async () => {
      mockApiCall.mockRejectedValue(new Error('boom'));

      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      expect(logic.error.value).toBe('boom');
      expect(logic.devices.value).toEqual([]);
      expect(logic.loading.value).toBe(false);
    });

    it('falls back to a generic error message when the thrown error has no message', async () => {
      mockApiCall.mockRejectedValue({});

      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      expect(logic.error.value).toBe('Failed to load devices');
      expect(logic.devices.value).toEqual([]);
    });

    it('toggles loading true during the in-flight fetch and false after', async () => {
      let release;
      mockApiCall.mockImplementation(
        () =>
          new Promise((resolve) => {
            release = resolve;
          })
      );

      const { logic } = mountLogic();
      await nextTick();
      expect(logic.loading.value).toBe(true);

      release({ devices: sampleDevices });
      await nextTick();
      await nextTick();
      expect(logic.loading.value).toBe(false);
    });
  });

  describe('computed properties', () => {
    it('currentDevice is the is_current device, otherDevices are the rest', async () => {
      mockApiCall.mockResolvedValue({ devices: sampleDevices });

      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      expect(logic.currentDevice.value).toEqual(sampleDevices[0]);
      expect(logic.otherDevices.value).toEqual([sampleDevices[1]]);
      expect(logic.hasOtherDevices.value).toBe(true);
      expect(logic.deviceCount.value).toBe(2);
    });

    it('currentDevice is null when no device is current', async () => {
      mockApiCall.mockResolvedValue({
        devices: [{ ...sampleDevices[1] }],
      });

      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      expect(logic.currentDevice.value).toBeNull();
      expect(logic.hasOtherDevices.value).toBe(true);
      expect(logic.deviceCount.value).toBe(1);
    });

    it('hasOtherDevices is false and deviceCount 0 with an empty list', async () => {
      mockApiCall.mockResolvedValue({ devices: [] });

      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      expect(logic.otherDevices.value).toEqual([]);
      expect(logic.hasOtherDevices.value).toBe(false);
      expect(logic.deviceCount.value).toBe(0);
    });
  });

  describe('revokeDevice', () => {
    it('DELETEs the device endpoint, toggles revoking, then refetches', async () => {
      // Initial mount fetch.
      mockApiCall.mockResolvedValue({ devices: sampleDevices });
      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      // Reset call count after the onMounted fetch.
      mockApiCall.mockClear();

      // First call = the DELETE, second call = the refetch.
      let releaseDelete;
      mockApiCall
        .mockImplementationOnce(
          () =>
            new Promise((resolve) => {
              releaseDelete = resolve;
            })
        )
        .mockResolvedValueOnce({ devices: [sampleDevices[0]] });

      const promise = logic.revokeDevice(2);
      await nextTick();
      expect(logic.revoking.value).toBe(2);

      releaseDelete(null);
      await promise;

      expect(mockApiCall).toHaveBeenNthCalledWith(1, '/authn/devices/2/revoke/', {
        method: 'DELETE',
      });
      // The refetch ran.
      expect(mockApiCall).toHaveBeenNthCalledWith(2, '/authn/devices/', { method: 'GET' });
      expect(mockApiCall).toHaveBeenCalledTimes(2);
      expect(logic.revoking.value).toBeNull();
    });

    it('sets error and resets revoking when the DELETE throws', async () => {
      mockApiCall.mockResolvedValue({ devices: sampleDevices });
      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      mockApiCall.mockClear();
      mockApiCall.mockRejectedValueOnce(new Error('revoke failed'));

      await logic.revokeDevice(2);

      expect(logic.error.value).toBe('revoke failed');
      expect(logic.revoking.value).toBeNull();
      // No refetch happened because the DELETE threw.
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });
  });

  describe('revokeAllOtherDevices', () => {
    it('DELETEs revoke-all, sets revoking to "all", then refetches', async () => {
      mockApiCall.mockResolvedValue({ devices: sampleDevices });
      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      mockApiCall.mockClear();

      let releaseDelete;
      mockApiCall
        .mockImplementationOnce(
          () =>
            new Promise((resolve) => {
              releaseDelete = resolve;
            })
        )
        .mockResolvedValueOnce({ devices: [sampleDevices[0]] });

      const promise = logic.revokeAllOtherDevices();
      await nextTick();
      expect(logic.revoking.value).toBe('all');

      releaseDelete(null);
      await promise;

      expect(mockApiCall).toHaveBeenNthCalledWith(1, '/authn/devices/revoke-all/', {
        method: 'DELETE',
      });
      expect(mockApiCall).toHaveBeenNthCalledWith(2, '/authn/devices/', { method: 'GET' });
      expect(mockApiCall).toHaveBeenCalledTimes(2);
      expect(logic.revoking.value).toBeNull();
    });

    it('sets error and resets revoking when revoke-all throws', async () => {
      mockApiCall.mockResolvedValue({ devices: sampleDevices });
      const { logic } = mountLogic();
      await nextTick();
      await nextTick();

      mockApiCall.mockClear();
      mockApiCall.mockRejectedValueOnce(new Error('all failed'));

      await logic.revokeAllOtherDevices();

      expect(logic.error.value).toBe('all failed');
      expect(logic.revoking.value).toBeNull();
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });
  });

  describe('getDeviceIcon', () => {
    it('maps known device types to Material icon names', () => {
      mockApiCall.mockResolvedValue({ devices: [] });
      const { logic } = mountLogic();

      expect(logic.getDeviceIcon('mobile')).toBe('smartphone');
      expect(logic.getDeviceIcon('tablet')).toBe('tablet');
      expect(logic.getDeviceIcon('desktop')).toBe('computer');
    });

    it('falls back to "devices" for unknown types', () => {
      mockApiCall.mockResolvedValue({ devices: [] });
      const { logic } = mountLogic();

      expect(logic.getDeviceIcon('unknown')).toBe('devices');
      expect(logic.getDeviceIcon('')).toBe('devices');
    });
  });

  describe('date formatters', () => {
    it('formatRelativeTime returns "Unknown" for a falsy value', () => {
      mockApiCall.mockResolvedValue({ devices: [] });
      const { logic } = mountLogic();

      expect(logic.formatRelativeTime('')).toBe('Unknown');
    });

    it('formatExpirationTime returns "Unknown" for a falsy value', () => {
      mockApiCall.mockResolvedValue({ devices: [] });
      const { logic } = mountLogic();

      expect(logic.formatExpirationTime('')).toBe('Unknown');
    });

    it('formatExpirationTime returns "Expired" for a past timestamp', () => {
      mockApiCall.mockResolvedValue({ devices: [] });
      const { logic } = mountLogic();

      // Build a timestamp clearly in the past relative to now.
      const past = new Date(Date.now() - 60 * 60 * 1000).toISOString();
      expect(logic.formatExpirationTime(past)).toBe('Expired');
    });

    it('formatExpirationTime returns an "Expires in" string for a future timestamp', () => {
      mockApiCall.mockResolvedValue({ devices: [] });
      const { logic } = mountLogic();

      // Build a timestamp clearly in the future relative to now.
      const future = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString();
      expect(logic.formatExpirationTime(future)).toMatch(/^Expires in /);
    });

    it('formatDateTime returns "Unknown" for a falsy value', () => {
      mockApiCall.mockResolvedValue({ devices: [] });
      const { logic } = mountLogic();

      expect(logic.formatDateTime('')).toBe('Unknown');
    });

    it('formatDateTime returns a non-empty formatted string for a valid date', () => {
      mockApiCall.mockResolvedValue({ devices: [] });
      const { logic } = mountLogic();

      const result = logic.formatDateTime('2026-01-01T12:30:00Z');
      expect(typeof result).toBe('string');
      expect(result).not.toBe('Unknown');
      expect(result.length).toBeGreaterThan(0);
    });
  });
});
