import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const mockApiGenerateBarcode = vi.fn();
const mockApiGetActiveProfile = vi.fn();
const mockApiGetBarcodeDashboard = vi.fn();
const mockLoadAvatar = vi.fn(async () => {});
const mockLoadUserProfile = vi.fn(async () => {});
const mockUserInfo = vi.fn();
const mockSetUserInfo = vi.fn();

vi.mock('@shared/api/auth', () => ({
  userInfo: () => mockUserInfo(),
}));

vi.mock('@shared/state/authState', () => ({
  getUserInfo: vi.fn(() => ({ profile: { name: 'Cached User', information_id: 'ID-1' } })),
  setUserInfo: (value) => mockSetUserInfo(value),
}));

vi.mock('@user/composables/useUserInfo', () => ({
  useUserInfo: () => ({
    profile: ref({ name: 'Cached User', information_id: 'ID-1' }),
    avatarSrc: ref(''),
    loadAvatar: mockLoadAvatar,
    loadUserProfile: mockLoadUserProfile,
  }),
}));

vi.mock('@auth/composables/useToken', () => ({
  useToken: () => ({
    isRefreshingToken: ref(false),
  }),
}));

vi.mock('@shared/composables/useApi', () => ({
  useApi: () => ({
    apiGenerateBarcode: mockApiGenerateBarcode,
    apiGetActiveProfile: mockApiGetActiveProfile,
    apiGetBarcodeDashboard: mockApiGetBarcodeDashboard,
  }),
}));

describe('useHomeLogic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the generated barcode sequence and resumes detection after success', async () => {
    mockApiGenerateBarcode.mockResolvedValue({
      status: 'success',
      barcode: 'ABC123',
      message: 'Identification barcode',
      profile_info: {
        name: 'Updated User',
        information_id: 'NEW-1',
        avatar_data: 'data:image/png;base64,abc',
      },
    });

    const { useHomeLogic } = await import('@home/composables/useHomeLogic.js');
    const logic = useHomeLogic();
    const renderBarcodeSequence = vi.fn(async () => {});
    const startDetection = vi.fn(async () => {});

    logic.scannerDetectionEnabled.value = true;
    logic.barcodeDisplayRef.value = {
      renderBarcodeSequence,
      startDetection,
    };

    await logic.handleGenerate();

    expect(renderBarcodeSequence).toHaveBeenCalledWith('ABC123', {
      displayDuration: 10000,
    });
    expect(startDetection).toHaveBeenCalledTimes(1);
    expect(logic.serverStatus.value).toBe('Emergency');
    expect(logic.profile.value).toEqual({
      name: 'Updated User',
      information_id: 'NEW-1',
    });
    expect(logic.avatarSrc.value).toBe('data:image/png;base64,abc');
  });

  it('shows a display error and resumes detection when barcode rendering fails', async () => {
    mockApiGenerateBarcode.mockResolvedValue({
      status: 'success',
      barcode: 'ABC123',
      message: 'Identification barcode',
    });

    const { useHomeLogic } = await import('@home/composables/useHomeLogic.js');
    const logic = useHomeLogic();
    const startDetection = vi.fn(async () => {});

    logic.scannerDetectionEnabled.value = true;
    logic.barcodeDisplayRef.value = {
      renderBarcodeSequence: vi.fn(async () => {
        throw new Error('render failed');
      }),
      startDetection,
    };

    await logic.handleGenerate();

    expect(logic.serverStatus.value).toBe('Unable to display barcode');
    expect(startDetection).toHaveBeenCalledTimes(1);
  });
});
