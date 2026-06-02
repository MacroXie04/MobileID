import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, nextTick } from 'vue';
import { mount } from '@vue/test-utils';

// --- vue-router mock ---
const mockRouterReplace = vi.fn(() => Promise.resolve());
let mockRoute = { query: {} as Record<string, unknown> };
vi.mock('vue-router', () => ({
  useRouter: () => ({ replace: (arg: unknown) => mockRouterReplace(arg) }),
  useRoute: () => mockRoute,
}));

// --- @barcode mock (useBarcodeApi + useDailyLimit) ---
const {
  mockApiGetBarcodeDashboard,
  mockApiUpdateBarcodeSettings,
  mockApiDeleteBarcode,
  mockApiUpdateBarcodeShare,
  mockApiUpdateBarcodeDailyLimit,
} = vi.hoisted(() => ({
  mockApiGetBarcodeDashboard: vi.fn(),
  mockApiUpdateBarcodeSettings: vi.fn(),
  mockApiDeleteBarcode: vi.fn(),
  mockApiUpdateBarcodeShare: vi.fn(),
  mockApiUpdateBarcodeDailyLimit: vi.fn(),
}));

vi.mock('@barcode', () => ({
  useBarcodeApi: () => ({
    apiGetBarcodeDashboard: mockApiGetBarcodeDashboard,
    apiUpdateBarcodeSettings: mockApiUpdateBarcodeSettings,
    apiDeleteBarcode: mockApiDeleteBarcode,
    apiUpdateBarcodeShare: mockApiUpdateBarcodeShare,
    apiUpdateBarcodeDailyLimit: mockApiUpdateBarcodeDailyLimit,
  }),
  // Inert daily-limit composable so the logic composable can construct.
  useDailyLimit: () => ({
    updatingLimit: { value: {} },
    updateDailyLimit: vi.fn(),
    incrementDailyLimit: vi.fn(),
    decrementDailyLimit: vi.fn(),
    toggleUnlimitedSwitch: vi.fn(),
    applyLimitPreset: vi.fn(),
  }),
}));

// Import after mocks are registered.
import { useDashboardLogic } from '@dashboard/composables/useDashboardLogic';

type DashboardLogic = ReturnType<typeof useDashboardLogic>;

/**
 * Mount a tiny harness so onMounted/onUnmounted/watch actually fire with an
 * active component instance, and expose the composable result via vm.logic.
 */
function mountLogic(): { logic: DashboardLogic; wrapper: ReturnType<typeof mount> } {
  let captured: DashboardLogic;
  const Harness = defineComponent({
    setup(_props, { expose }) {
      captured = useDashboardLogic();
      expose({ logic: captured });
      return () => null;
    },
  });
  const wrapper = mount(Harness);
  // @ts-expect-error captured is assigned synchronously inside setup
  return { logic: captured, wrapper };
}

function dashboardPayload(overrides: Record<string, unknown> = {}) {
  return {
    settings: {
      associate_user_profile_with_barcode: 1,
      scanner_detection_enabled: 0,
      prefer_front_camera: false,
      barcode: 'x',
      barcode_choices: [
        { id: 'x', barcode: '11112222', barcode_type: 'DynamicBarcode' },
        { id: 'y', barcode: '99998888', barcode_type: 'Others' },
      ],
    },
    pull_settings: { pull_setting: 'Enable', gender_setting: 'Male' },
    barcodes: [
      {
        barcode_uuid: 'x',
        barcode: '11112222',
        barcode_type: 'DynamicBarcode',
        is_owned_by_current_user: true,
        share_with_others: false,
      },
      {
        barcode_uuid: 'y',
        barcode: '99998888',
        barcode_type: 'Others',
        is_owned_by_current_user: false,
        share_with_others: false,
      },
    ],
    ...overrides,
  };
}

describe('useDashboardLogic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute = { query: {} };
    // Default: dashboard load resolves with no usable data so onMounted's
    // loadDashboard() does not blow up. Individual tests override as needed.
    mockApiGetBarcodeDashboard.mockResolvedValue({ settings: {}, barcodes: [] });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('tabs', () => {
    it('defaults activeTab to "Overview"', async () => {
      const { logic } = mountLogic();
      await nextTick();
      expect(logic.activeTab.value).toBe('Overview');
    });

    it('reads route.query.tab from the allow-list on mount', async () => {
      mockRoute = { query: { tab: 'Devices' } };
      const { logic } = mountLogic();
      await nextTick();
      expect(logic.activeTab.value).toBe('Devices');
    });

    it('ignores an invalid route.query.tab and stays on "Overview"', async () => {
      mockRoute = { query: { tab: 'NotARealTab' } };
      const { logic } = mountLogic();
      await nextTick();
      expect(logic.activeTab.value).toBe('Overview');
    });

    it('replaces the router query when activeTab changes', async () => {
      mockRoute = { query: { foo: 'bar' } };
      const { logic } = mountLogic();
      await nextTick();
      mockRouterReplace.mockClear();

      logic.activeTab.value = 'Barcodes';
      await nextTick();

      expect(mockRouterReplace).toHaveBeenCalledWith({
        query: { foo: 'bar', tab: 'Barcodes' },
      });
    });

    it('setTab sets activeTab and goToAddTab selects the Add tab', async () => {
      const { logic } = mountLogic();
      await nextTick();

      logic.setTab('Profile');
      expect(logic.activeTab.value).toBe('Profile');

      logic.goToAddTab();
      expect(logic.activeTab.value).toBe('Add');
    });
  });

  describe('loadDashboard', () => {
    it('coerces settings booleans, populates choices/barcodes and maps pull settings', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      const { logic } = mountLogic();
      // onMounted runs loadDashboard; flush its awaited microtasks.
      await flushAsync();

      expect(logic.settings.value.associate_user_profile_with_barcode).toBe(true);
      expect(logic.settings.value.scanner_detection_enabled).toBe(false);
      expect(logic.settings.value.prefer_front_camera).toBe(false);
      expect(logic.settings.value.barcode).toBe('x');

      expect(logic.barcodeChoices.value).toHaveLength(2);
      expect(logic.barcodes.value).toHaveLength(2);

      expect(logic.pullSettings.value.pull_setting).toBe('Enable');
      expect(logic.pullSettings.value.gender_setting).toBe('Male');

      expect(logic.loading.value).toBe(false);
    });

    it('shows a danger message when the dashboard request rejects', async () => {
      mockApiGetBarcodeDashboard.mockRejectedValue({ message: 'boom' });
      const { logic } = mountLogic();
      await flushAsync();

      expect(logic.message.value).toContain('Failed to load dashboard');
      expect(logic.messageType.value).toBe('danger');
      expect(logic.loading.value).toBe(false);
    });
  });

  describe('filteredBarcodes / hasActiveFilters', () => {
    async function loadedLogic() {
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      const { logic } = mountLogic();
      await flushAsync();
      return logic;
    }

    it('returns all barcodes with default filters and no active filters', async () => {
      const logic = await loadedLogic();
      expect(logic.filteredBarcodes.value).toHaveLength(2);
      expect(logic.hasActiveFilters.value).toBe(false);
    });

    it('filters to Dynamic barcodes', async () => {
      const logic = await loadedLogic();
      logic.filterType.value = 'Dynamic';
      await nextTick();
      expect(logic.filteredBarcodes.value).toHaveLength(1);
      expect(logic.filteredBarcodes.value[0].barcode_type).toBe('DynamicBarcode');
      expect(logic.hasActiveFilters.value).toBe(true);
    });

    it('filters to Static (Others) barcodes', async () => {
      const logic = await loadedLogic();
      logic.filterType.value = 'Static';
      await nextTick();
      expect(logic.filteredBarcodes.value).toHaveLength(1);
      expect(logic.filteredBarcodes.value[0].barcode_type).toBe('Others');
      expect(logic.hasActiveFilters.value).toBe(true);
    });

    it('filters to owned-only barcodes', async () => {
      const logic = await loadedLogic();
      logic.ownedOnly.value = true;
      await nextTick();
      expect(logic.filteredBarcodes.value).toHaveLength(1);
      expect(logic.filteredBarcodes.value[0].is_owned_by_current_user).toBe(true);
      expect(logic.hasActiveFilters.value).toBe(true);
    });
  });

  describe('currentBarcodeInfo', () => {
    it('describes the selected choice with its last 4 digits', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      const { logic } = mountLogic();
      await flushAsync();

      // selected barcode is 'x' -> DynamicBarcode ending with 2222
      expect(logic.currentBarcodeInfo.value).toBe('DynamicBarcode ending with ...2222');
    });

    it('is null when no barcode is selected', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(
        dashboardPayload({
          settings: {
            barcode: null,
            barcode_choices: [],
          },
        })
      );
      const { logic } = mountLogic();
      await flushAsync();
      expect(logic.currentBarcodeInfo.value).toBeNull();
    });
  });

  describe('setActiveBarcode', () => {
    it('is blocked with a message when pull_setting is "Enable"', async () => {
      // payload pull_setting is 'Enable'
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      const { logic } = mountLogic();
      await flushAsync();
      mockApiUpdateBarcodeSettings.mockClear();

      await logic.setActiveBarcode({ barcode_uuid: 'y', barcode: '99998888' });

      expect(mockApiUpdateBarcodeSettings).not.toHaveBeenCalled();
      expect(logic.message.value).toMatch(/pull setting is enabled/i);
      expect(logic.messageType.value).toBe('danger');
    });

    it('is a no-op when the barcode is already active', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(
        dashboardPayload({ pull_settings: { pull_setting: 'Disable', gender_setting: 'Male' } })
      );
      const { logic } = mountLogic();
      await flushAsync();
      mockApiUpdateBarcodeSettings.mockClear();

      // currently active barcode is 'x'
      await logic.setActiveBarcode({ barcode_uuid: 'x', barcode: '11112222' });

      expect(mockApiUpdateBarcodeSettings).not.toHaveBeenCalled();
    });

    it('sets the barcode and triggers a save when allowed and different', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(
        dashboardPayload({ pull_settings: { pull_setting: 'Disable', gender_setting: 'Male' } })
      );
      mockApiUpdateBarcodeSettings.mockResolvedValue({ status: 'success' });
      const { logic } = mountLogic();
      await flushAsync();
      mockApiUpdateBarcodeSettings.mockClear();

      await logic.setActiveBarcode({ barcode_uuid: 'y', barcode: '99998888' });

      expect(logic.settings.value.barcode).toBe('y');
      expect(mockApiUpdateBarcodeSettings).toHaveBeenCalledTimes(1);
    });
  });

  describe('deleteBarcode / confirmDelete', () => {
    it('rejects deletion of a barcode not owned by the current user', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      const { logic } = mountLogic();
      await flushAsync();

      await logic.deleteBarcode({ barcode_uuid: 'y', is_owned_by_current_user: false });

      expect(logic.message.value).toBe('You can only delete your own barcode');
      expect(logic.messageType.value).toBe('danger');
      expect(logic.showConfirmDialog.value).toBe(false);
    });

    it('opens the confirmation dialog for an owned barcode', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      const { logic } = mountLogic();
      await flushAsync();

      await logic.deleteBarcode({ barcode_uuid: 'x', is_owned_by_current_user: true });

      expect(logic.showConfirmDialog.value).toBe(true);
      expect(logic.barcodeToDelete.value).toBe('x');
    });

    it('confirmDelete deletes then reloads the dashboard on success', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      mockApiDeleteBarcode.mockResolvedValue({ status: 'success', message: 'Deleted' });
      const { logic } = mountLogic();
      await flushAsync();

      await logic.deleteBarcode({ barcode_uuid: 'x', is_owned_by_current_user: true });
      mockApiGetBarcodeDashboard.mockClear();

      await logic.confirmDelete();
      await flushAsync();

      expect(mockApiDeleteBarcode).toHaveBeenCalledWith('x');
      expect(mockApiGetBarcodeDashboard).toHaveBeenCalledTimes(1);
      expect(logic.showConfirmDialog.value).toBe(false);
      expect(logic.barcodeToDelete.value).toBeNull();
    });
  });

  describe('toggleShare', () => {
    it('optimistically updates share_with_others from the server echo', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      mockApiUpdateBarcodeShare.mockResolvedValue({
        status: 'success',
        barcode: { share_with_others: true },
      });
      const { logic } = mountLogic();
      await flushAsync();

      const owned = logic.barcodes.value.find((b) => b.barcode_uuid === 'x');
      await logic.toggleShare(owned);

      expect(mockApiUpdateBarcodeShare).toHaveBeenCalledWith('x', true);
      const updated = logic.barcodes.value.find((b) => b.barcode_uuid === 'x');
      expect(updated.share_with_others).toBe(true);
      expect(logic.message.value).toBe('Sharing enabled');
    });

    it('does nothing for a barcode not owned by the current user', async () => {
      mockApiGetBarcodeDashboard.mockResolvedValue(dashboardPayload());
      const { logic } = mountLogic();
      await flushAsync();

      await logic.toggleShare({ barcode_uuid: 'y', is_owned_by_current_user: false });

      expect(mockApiUpdateBarcodeShare).not.toHaveBeenCalled();
    });
  });

  describe('onSettingChange debounce', () => {
    it('calls apiUpdateBarcodeSettings once after 800ms despite rapid calls', async () => {
      vi.useFakeTimers();
      mockApiGetBarcodeDashboard.mockResolvedValue({ settings: {}, barcodes: [] });
      mockApiUpdateBarcodeSettings.mockResolvedValue({ status: 'success' });

      const { logic } = mountLogic();
      // Let onMounted's loadDashboard settle without advancing the debounce.
      await vi.advanceTimersByTimeAsync(0);
      mockApiUpdateBarcodeSettings.mockClear();

      logic.onSettingChange();
      vi.advanceTimersByTime(300);
      logic.onSettingChange();
      vi.advanceTimersByTime(300);
      logic.onSettingChange();

      expect(mockApiUpdateBarcodeSettings).not.toHaveBeenCalled();

      await vi.advanceTimersByTimeAsync(800);

      expect(mockApiUpdateBarcodeSettings).toHaveBeenCalledTimes(1);
    });
  });
});

/**
 * Flush queued microtasks (awaited promises inside loadDashboard, including
 * its internal nextTick) without relying on fake timers.
 */
async function flushAsync() {
  for (let i = 0; i < 5; i += 1) {
    await Promise.resolve();
    await nextTick();
  }
}
