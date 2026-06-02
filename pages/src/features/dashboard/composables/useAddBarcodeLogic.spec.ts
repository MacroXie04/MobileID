import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

// Mock the entire @barcode module: useBarcodeApi exposes the three API calls the
// composable destructures; useBarcodeScanner is inert (owns the lifecycle hooks,
// so mocking it lets us call useAddBarcodeLogic directly without a harness).
const {
  mockApiCreateBarcode,
  mockApiCreateDynamicBarcodeWithProfile,
  mockApiTransferDynamicBarcode,
} = vi.hoisted(() => ({
  mockApiCreateBarcode: vi.fn(),
  mockApiCreateDynamicBarcodeWithProfile: vi.fn(),
  mockApiTransferDynamicBarcode: vi.fn(),
}));

vi.mock('@barcode', () => ({
  useBarcodeApi: () => ({
    apiCreateBarcode: (...args: unknown[]) => mockApiCreateBarcode(...args),
    apiCreateDynamicBarcodeWithProfile: (...args: unknown[]) =>
      mockApiCreateDynamicBarcodeWithProfile(...args),
    apiTransferDynamicBarcode: (...args: unknown[]) => mockApiTransferDynamicBarcode(...args),
  }),
  useBarcodeScanner: () => ({
    showScanner: ref(false),
    scanning: ref(false),
    scannerStatus: ref(''),
    videoRef: ref(null),
    cameras: ref([]),
    selectedCameraId: ref(null),
    toggleScanner: vi.fn(),
    hasCameraPermission: ref(false),
    ensureCameraPermission: vi.fn(),
  }),
}));

// Import after mocks are registered.
import { useAddBarcodeLogic } from '@dashboard/composables/useAddBarcodeLogic';

// Build an AuthenticatedRequestError-shaped plain object for rejections.
function authError({
  status,
  errors,
  message,
}: {
  status?: number;
  errors?: Record<string, string | string[]>;
  message?: string;
}) {
  return { status, errors, message };
}

describe('useAddBarcodeLogic', () => {
  let emit;

  beforeEach(() => {
    vi.clearAllMocks();
    emit = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('addBarcode', () => {
    it('sets a required error and skips the API call when newBarcode is empty', async () => {
      const logic = useAddBarcodeLogic(emit);
      logic.newBarcode.value = '   ';

      await logic.addBarcode();

      expect(logic.errors.value.newBarcode).toBe('Barcode is required');
      expect(mockApiCreateBarcode).not.toHaveBeenCalled();
      expect(emit).not.toHaveBeenCalled();
    });

    it('on success emits message + added and clears newBarcode', async () => {
      mockApiCreateBarcode.mockResolvedValue({ status: 'success', message: 'Barcode added!' });
      const logic = useAddBarcodeLogic(emit);
      logic.newBarcode.value = '123';

      await logic.addBarcode();

      expect(mockApiCreateBarcode).toHaveBeenCalledWith('123');
      expect(emit).toHaveBeenCalledWith('message', 'Barcode added!', 'success');
      expect(logic.newBarcode.value).toBe('');
      expect(emit).toHaveBeenCalledWith('added');
    });

    it('maps a 400 with errors.barcode array to the field error', async () => {
      mockApiCreateBarcode.mockRejectedValue(
        authError({ status: 400, errors: { barcode: ['taken'] } })
      );
      const logic = useAddBarcodeLogic(emit);
      logic.newBarcode.value = '123';

      await logic.addBarcode();

      expect(logic.errors.value.newBarcode).toBe('taken');
      expect(emit).not.toHaveBeenCalled();
    });

    it('reports "Barcode already exists" for a 400 message without errors.barcode', async () => {
      mockApiCreateBarcode.mockRejectedValue(
        authError({
          status: 400,
          errors: { other: ['x'] },
          message: 'barcode with this barcode already exists in the system',
        })
      );
      const logic = useAddBarcodeLogic(emit);
      logic.newBarcode.value = '123';

      await logic.addBarcode();

      expect(logic.errors.value.newBarcode).toBe('Barcode already exists');
    });

    it('reports "Invalid barcode" for a 400 with errors but an empty barcode array', async () => {
      mockApiCreateBarcode.mockRejectedValue(authError({ status: 400, errors: { barcode: [] } }));
      const logic = useAddBarcodeLogic(emit);
      logic.newBarcode.value = '123';

      await logic.addBarcode();

      expect(logic.errors.value.newBarcode).toBe('Invalid barcode');
    });

    it('emits a danger message for non-400 failures', async () => {
      mockApiCreateBarcode.mockRejectedValue(authError({ status: 500, message: 'boom' }));
      const logic = useAddBarcodeLogic(emit);
      logic.newBarcode.value = '123';

      await logic.addBarcode();

      expect(emit).toHaveBeenCalledWith('message', 'Failed to add barcode', 'danger');
      expect(logic.errors.value.newBarcode).toBeUndefined();
    });
  });

  describe('clearError', () => {
    it('removes a single field from errors', () => {
      const logic = useAddBarcodeLogic(emit);
      logic.errors.value = { newBarcode: 'Barcode is required', other: 'x' };

      logic.clearError('newBarcode');

      expect(logic.errors.value.newBarcode).toBeUndefined();
      expect(logic.errors.value.other).toBe('x');
    });
  });

  describe('createDynamicBarcode validation', () => {
    it('rejects a non-numeric barcode without calling the API', async () => {
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicBarcode.value = 'abcd';
      logic.dynamicName.value = 'Jane';
      logic.dynamicInformationId.value = '999';

      await logic.createDynamicBarcode();

      expect(logic.dynamicErrors.value.barcode).toBe('Barcode must contain only digits');
      expect(mockApiCreateDynamicBarcodeWithProfile).not.toHaveBeenCalled();
    });

    it('rejects a barcode that is not exactly 14 digits', async () => {
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicBarcode.value = '12345';
      logic.dynamicName.value = 'Jane';
      logic.dynamicInformationId.value = '999';

      await logic.createDynamicBarcode();

      expect(logic.dynamicErrors.value.barcode).toBe('Barcode must be exactly 14 digits');
      expect(mockApiCreateDynamicBarcodeWithProfile).not.toHaveBeenCalled();
    });

    it('requires a name', async () => {
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicBarcode.value = '12345678901234';
      logic.dynamicName.value = '';
      logic.dynamicInformationId.value = '999';

      await logic.createDynamicBarcode();

      expect(logic.dynamicErrors.value.name).toBe('Name is required');
      expect(mockApiCreateDynamicBarcodeWithProfile).not.toHaveBeenCalled();
    });

    it('requires an information_id (Student ID)', async () => {
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicBarcode.value = '12345678901234';
      logic.dynamicName.value = 'Jane';
      logic.dynamicInformationId.value = '';

      await logic.createDynamicBarcode();

      expect(logic.dynamicErrors.value.information_id).toBe('Student ID is required');
      expect(mockApiCreateDynamicBarcodeWithProfile).not.toHaveBeenCalled();
    });
  });

  describe('createDynamicBarcode success', () => {
    it('calls the API with trimmed payload, emits message + added, and clears fields', async () => {
      mockApiCreateDynamicBarcodeWithProfile.mockResolvedValue({
        status: 'success',
        message: 'Profile created!',
      });
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicBarcode.value = ' 12345678901234 ';
      logic.dynamicName.value = ' Jane ';
      logic.dynamicInformationId.value = ' 999 ';
      logic.dynamicGender.value = 'Female';
      logic.dynamicAvatar.value = ' data:image ';

      await logic.createDynamicBarcode();

      expect(mockApiCreateDynamicBarcodeWithProfile).toHaveBeenCalledWith({
        barcode: '12345678901234',
        name: 'Jane',
        information_id: '999',
        gender: 'Female',
        avatar: 'data:image',
      });
      expect(logic.dynamicSuccess.value).toBe(true);
      expect(logic.dynamicSuccessMessage.value).toBe('Profile created!');
      expect(emit).toHaveBeenCalledWith('message', 'Profile created!', 'success');
      expect(emit).toHaveBeenCalledWith('added');
      expect(logic.dynamicBarcode.value).toBe('');
      expect(logic.dynamicName.value).toBe('');
      expect(logic.dynamicInformationId.value).toBe('');
      expect(logic.dynamicGender.value).toBe('Unknow');
      expect(logic.dynamicAvatar.value).toBe('');
      expect(logic.dynamicLoading.value).toBe(false);
    });

    it('omits avatar from the payload when it is blank', async () => {
      mockApiCreateDynamicBarcodeWithProfile.mockResolvedValue({ status: 'success' });
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicBarcode.value = '12345678901234';
      logic.dynamicName.value = 'Jane';
      logic.dynamicInformationId.value = '999';
      logic.dynamicAvatar.value = '   ';

      await logic.createDynamicBarcode();

      expect(mockApiCreateDynamicBarcodeWithProfile).toHaveBeenCalledWith({
        barcode: '12345678901234',
        name: 'Jane',
        information_id: '999',
        gender: 'Unknow',
      });
    });
  });

  describe('createDynamicBarcode error handling', () => {
    it('maps 400 field errors into dynamicErrors and a joined dynamicError', async () => {
      mockApiCreateDynamicBarcodeWithProfile.mockRejectedValue(
        authError({
          status: 400,
          errors: {
            barcode: ['bad barcode'],
            name: 'bad name',
            information_id: ['bad id'],
            avatar: ['bad avatar'],
          },
        })
      );
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicBarcode.value = '12345678901234';
      logic.dynamicName.value = 'Jane';
      logic.dynamicInformationId.value = '999';

      await logic.createDynamicBarcode();

      expect(logic.dynamicErrors.value.barcode).toBe('bad barcode');
      expect(logic.dynamicErrors.value.name).toBe('bad name');
      expect(logic.dynamicErrors.value.information_id).toBe('bad id');
      expect(logic.dynamicErrors.value.avatar).toBe('bad avatar');
      expect(logic.dynamicError.value).toBe(
        'Barcode: bad barcode; Name: bad name; Student ID: bad id; Avatar: bad avatar'
      );
      expect(logic.dynamicLoading.value).toBe(false);
    });

    it('reports a permission-denied message on 403', async () => {
      mockApiCreateDynamicBarcodeWithProfile.mockRejectedValue(authError({ status: 403 }));
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicBarcode.value = '12345678901234';
      logic.dynamicName.value = 'Jane';
      logic.dynamicInformationId.value = '999';

      await logic.createDynamicBarcode();

      expect(logic.dynamicError.value).toBe('Permission denied. Please ensure you are logged in.');
    });
  });

  describe('clearDynamicError', () => {
    it('removes a single field and resets dynamic success/error state', () => {
      const logic = useAddBarcodeLogic(emit);
      logic.dynamicErrors.value = { barcode: 'bad', name: 'keep' };
      logic.dynamicError.value = 'something';
      logic.dynamicSuccess.value = true;
      logic.dynamicSuccessMessage.value = 'yay';

      logic.clearDynamicError('barcode');

      expect(logic.dynamicErrors.value.barcode).toBeUndefined();
      expect(logic.dynamicErrors.value.name).toBe('keep');
      expect(logic.dynamicError.value).toBe('');
      expect(logic.dynamicSuccess.value).toBe(false);
      expect(logic.dynamicSuccessMessage.value).toBe('');
    });
  });

  describe('transferDynamicBarcode', () => {
    it('requires HTML content without calling the API', async () => {
      const logic = useAddBarcodeLogic(emit);
      logic.transferHtml.value = '   ';

      await logic.transferDynamicBarcode();

      expect(logic.transferErrors.value.html).toBe('HTML content is required');
      expect(mockApiTransferDynamicBarcode).not.toHaveBeenCalled();
    });

    it('on success emits message + added and clears the HTML field', async () => {
      mockApiTransferDynamicBarcode.mockResolvedValue({
        status: 'success',
        message: 'Transferred!',
      });
      const logic = useAddBarcodeLogic(emit);
      logic.transferHtml.value = '<html>x</html>';

      await logic.transferDynamicBarcode();

      expect(mockApiTransferDynamicBarcode).toHaveBeenCalledWith('<html>x</html>');
      expect(logic.transferSuccess.value).toBe(true);
      expect(logic.transferSuccessMessage.value).toBe('Transferred!');
      expect(emit).toHaveBeenCalledWith('message', 'Transferred!', 'success');
      expect(emit).toHaveBeenCalledWith('added');
      expect(logic.transferHtml.value).toBe('');
      expect(logic.transferLoading.value).toBe(false);
    });

    it('maps 400 field errors into transferErrors and a joined transferError', async () => {
      mockApiTransferDynamicBarcode.mockRejectedValue(
        authError({
          status: 400,
          errors: {
            html: ['bad html'],
            barcode: 'bad barcode',
            name: ['bad name'],
            information_id: 'bad id',
          },
        })
      );
      const logic = useAddBarcodeLogic(emit);
      logic.transferHtml.value = '<html>x</html>';

      await logic.transferDynamicBarcode();

      expect(logic.transferErrors.value.html).toBe('bad html');
      expect(logic.transferErrors.value.barcode).toBe('bad barcode');
      expect(logic.transferErrors.value.name).toBe('bad name');
      expect(logic.transferErrors.value.information_id).toBe('bad id');
      expect(logic.transferError.value).toBe(
        'bad html; Barcode: bad barcode; Name: bad name; Student ID: bad id'
      );
      expect(logic.transferLoading.value).toBe(false);
    });

    it('reports a permission-denied message on 403', async () => {
      mockApiTransferDynamicBarcode.mockRejectedValue(authError({ status: 403 }));
      const logic = useAddBarcodeLogic(emit);
      logic.transferHtml.value = '<html>x</html>';

      await logic.transferDynamicBarcode();

      expect(logic.transferError.value).toBe('Permission denied. Please ensure you are logged in.');
    });
  });

  describe('clearTransferError', () => {
    it('resets all transfer error and success state', () => {
      const logic = useAddBarcodeLogic(emit);
      logic.transferErrors.value = { html: 'bad' };
      logic.transferError.value = 'something';
      logic.transferSuccess.value = true;
      logic.transferSuccessMessage.value = 'yay';

      logic.clearTransferError();

      expect(logic.transferErrors.value).toEqual({});
      expect(logic.transferError.value).toBe('');
      expect(logic.transferSuccess.value).toBe(false);
      expect(logic.transferSuccessMessage.value).toBe('');
    });
  });
});
