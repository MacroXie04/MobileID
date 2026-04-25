import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick, ref } from 'vue';
import BarcodeDisplay from '@mobile-id/components/barcode-display/BarcodeDisplay.vue';

const mockDrawPdf417 = vi.fn();
const mockStartDetection = vi.fn(async () => {});
const mockStopDetection = vi.fn();

vi.mock('@barcode/composables/usePdf417', () => ({
  usePdf417: () => ({
    drawPdf417: mockDrawPdf417,
  }),
}));

vi.mock('@shared/composables/device/useScannerDetection', () => ({
  useScannerDetection: () => ({
    isDetectionActive: ref(false),
    isModelLoading: ref(false),
    hasCameraPermission: ref(true),
    startDetection: mockStartDetection,
    stopDetection: mockStopDetection,
    ensureCameraPermission: vi.fn(async () => true),
  }),
}));

function getRenderBarcodeSequence(wrapper) {
  return wrapper.vm.renderBarcodeSequence ?? wrapper.vm.$.exposed.renderBarcodeSequence;
}

describe('School BarcodeDisplay', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('shows the barcode only after rendering completes and restores the initial state after the countdown', async () => {
    vi.useFakeTimers();

    let resolveDraw;
    mockDrawPdf417.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveDraw = resolve;
        })
    );

    const wrapper = mount(BarcodeDisplay);
    const renderBarcodeSequence = getRenderBarcodeSequence(wrapper);

    const sequencePromise = renderBarcodeSequence('ABC123', { displayDuration: 1000 });

    await nextTick();
    expect(wrapper.get('#qrcode-div').attributes('aria-hidden')).toBe('true');
    expect(wrapper.get('#qrcode-code').attributes('aria-hidden')).toBe('true');

    resolveDraw();
    await Promise.resolve();
    await nextTick();

    expect(mockDrawPdf417).toHaveBeenCalledTimes(1);
    expect(wrapper.get('#qrcode-div').attributes('aria-hidden')).toBe('false');
    expect(wrapper.get('#qrcode-code').attributes('aria-hidden')).toBe('false');

    await vi.runAllTimersAsync();
    await sequencePromise;
    await nextTick();

    expect(wrapper.get('#qrcode-div').attributes('aria-hidden')).toBe('true');
    expect(wrapper.get('#qrcode-code').attributes('aria-hidden')).toBe('true');
  }, 15000);

  it('shows a render error instead of leaving a blank barcode area', async () => {
    mockDrawPdf417.mockRejectedValue(new Error('boom'));

    const wrapper = mount(BarcodeDisplay);
    const renderBarcodeSequence = getRenderBarcodeSequence(wrapper);

    await expect(renderBarcodeSequence('ABC123')).rejects.toThrow('boom');
    await nextTick();

    expect(wrapper.text()).toContain('Unable to display barcode');
    expect(wrapper.get('#qrcode-div').attributes('aria-hidden')).toBe('true');
    expect(wrapper.get('#qrcode-code').attributes('aria-hidden')).toBe('true');
  });
});
