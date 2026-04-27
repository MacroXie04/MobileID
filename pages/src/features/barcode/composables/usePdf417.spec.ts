import { beforeEach, describe, expect, it, vi } from 'vitest';

async function importPdf417Composable() {
  vi.resetModules();
  return import('@barcode/composables/usePdf417');
}

describe('usePdf417', () => {
  beforeEach(() => {
    document.head.innerHTML = '';
    delete window.libbcmath;
    delete window.PDF417;
    vi.restoreAllMocks();
  });

  it('uses an already-loaded global PDF417 renderer', async () => {
    const pdf417 = { init: vi.fn(), getBarcodeArray: vi.fn() };
    window.PDF417 = pdf417;

    const { usePdf417 } = await importPdf417Composable();
    const { ensurePdf417Ready, barcodeReady } = usePdf417();

    await expect(ensurePdf417Ready()).resolves.toBe(pdf417);
    expect(barcodeReady.value).toBe(true);
  });

  it('lazy-loads the barcode scripts in order', async () => {
    const appendedPaths = [];

    vi.spyOn(document.head, 'appendChild').mockImplementation((node) => {
      appendedPaths.push(new URL(node.src).pathname);

      setTimeout(() => {
        if (node.src.endsWith('/js/bcmath-min.js')) {
          window.libbcmath = {};
        } else {
          window.PDF417 = { init: vi.fn(), getBarcodeArray: vi.fn() };
        }
        node.dispatchEvent(new Event('load'));
      }, 0);

      return node;
    });

    const { usePdf417 } = await importPdf417Composable();
    const { ensurePdf417Ready } = usePdf417();

    await ensurePdf417Ready();

    expect(appendedPaths).toEqual(['/js/bcmath-min.js', '/js/pdf417-min.js']);
  });

  it('reuses a single in-flight loader promise', async () => {
    vi.spyOn(document.head, 'appendChild').mockImplementation((node) => {
      setTimeout(() => {
        if (node.src.endsWith('/js/bcmath-min.js')) {
          window.libbcmath = {};
        } else {
          window.PDF417 = { init: vi.fn(), getBarcodeArray: vi.fn() };
        }
        node.dispatchEvent(new Event('load'));
      }, 0);

      return node;
    });

    const { usePdf417 } = await importPdf417Composable();
    const { ensurePdf417Ready } = usePdf417();

    const [first, second] = await Promise.all([ensurePdf417Ready(), ensurePdf417Ready()]);

    expect(first).toBe(second);
    expect(document.head.appendChild).toHaveBeenCalledTimes(2);
  });

  it('rejects when a dependency script fails to load', async () => {
    vi.spyOn(document.head, 'appendChild').mockImplementation((node) => {
      setTimeout(() => {
        node.dispatchEvent(new Event('error'));
      }, 0);

      return node;
    });

    const { usePdf417 } = await importPdf417Composable();
    const { ensurePdf417Ready } = usePdf417();

    await expect(ensurePdf417Ready()).rejects.toThrow('Failed to load /js/bcmath-min.js');
  });

  it('renders a PDF417 canvas with the expected dimensions', async () => {
    const fillRect = vi.fn();
    const ctx = {
      fillStyle: '#000000',
      fillRect,
    };
    const canvas = {
      style: {},
      getContext: vi.fn(() => ctx),
    };

    window.PDF417 = {
      init: vi.fn(),
      getBarcodeArray: vi.fn(() => ({
        num_rows: 2,
        num_cols: 3,
        bcode: [
          [1, 0, 1],
          [0, 1, 0],
        ],
      })),
    };

    const { usePdf417 } = await importPdf417Composable();
    const { drawPdf417 } = usePdf417();

    const result = await drawPdf417(canvas, 'ABC123', {
      moduleWidth: 2,
      moduleHeight: 4,
    });

    expect(canvas.width).toBe(6);
    expect(canvas.height).toBe(8);
    expect(result).toEqual({
      width: 6,
      height: 8,
      rows: 2,
      cols: 3,
    });
    expect(fillRect).toHaveBeenCalledWith(0, 0, 6, 8);
    expect(fillRect).toHaveBeenCalledWith(0, 0, 2, 4);
    expect(fillRect).toHaveBeenCalledWith(4, 0, 2, 4);
    expect(fillRect).toHaveBeenCalledWith(2, 4, 2, 4);
  });

  it('throws when the canvas cannot provide a 2D context', async () => {
    window.PDF417 = {
      init: vi.fn(),
      getBarcodeArray: vi.fn(() => ({
        num_rows: 1,
        num_cols: 1,
        bcode: [[1]],
      })),
    };

    const { usePdf417 } = await importPdf417Composable();
    const { drawPdf417 } = usePdf417();

    await expect(
      drawPdf417(
        {
          style: {},
          getContext: vi.fn(() => null),
        },
        'ABC123'
      )
    ).rejects.toThrow('Canvas 2D context unavailable');
  });
});
