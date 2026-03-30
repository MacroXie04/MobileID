import { ref } from 'vue';

const BCMATH_SRC = '/js/bcmath-min.js';
const PDF417_SRC = '/js/pdf417-min.js';

let pdf417LoadPromise = null;

function isScriptReady(globalName) {
  return typeof window !== 'undefined' && typeof window[globalName] !== 'undefined';
}

function loadScript(src, globalName) {
  if (isScriptReady(globalName)) {
    return Promise.resolve(window[globalName]);
  }

  if (typeof document === 'undefined') {
    return Promise.reject(new Error(`Cannot load ${src} outside the browser`));
  }

  return new Promise((resolve, reject) => {
    const existingScript = document.querySelector(`script[data-src="${src}"]`);

    const handleReady = () => {
      if (isScriptReady(globalName)) {
        resolve(window[globalName]);
        return;
      }
      reject(new Error(`${src} loaded but ${globalName} is unavailable`));
    };

    const handleError = () => {
      reject(new Error(`Failed to load ${src}`));
    };

    if (existingScript) {
      existingScript.addEventListener('load', handleReady, { once: true });
      existingScript.addEventListener('error', handleError, { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.dataset.src = src;
    script.addEventListener('load', handleReady, { once: true });
    script.addEventListener('error', handleError, { once: true });
    document.head.appendChild(script);
  });
}

export function usePdf417() {
  const barcodeReady = ref(false);

  async function ensurePdf417Ready() {
    if (isScriptReady('PDF417')) {
      barcodeReady.value = true;
      return window.PDF417;
    }

    if (!pdf417LoadPromise) {
      pdf417LoadPromise = (async () => {
        await loadScript(BCMATH_SRC, 'libbcmath');
        await loadScript(PDF417_SRC, 'PDF417');
        return window.PDF417;
      })().catch((error) => {
        pdf417LoadPromise = null;
        throw error;
      });
    }

    const pdf417 = await pdf417LoadPromise;
    barcodeReady.value = true;
    return pdf417;
  }

  /**
   * Draw PDF417 barcode on canvas element
   * @param {HTMLCanvasElement} canvas - The canvas element to draw on
   * @param {string} text - The text to encode in the barcode
   * @param {Object} options - Drawing options (moduleWidth, moduleHeight)
   */
  async function drawPdf417(canvas, text, options = {}) {
    if (!canvas) {
      barcodeReady.value = false;
      throw new Error('Canvas element not found');
    }

    if (!text) {
      barcodeReady.value = false;
      throw new Error('Barcode text is required');
    }

    try {
      const pdf417 = await ensurePdf417Ready();

      // Initialize PDF417 with the barcode text
      pdf417.init(text);
      const barcodeArray = pdf417.getBarcodeArray();

      if (!barcodeArray || !barcodeArray.bcode || barcodeArray.num_rows <= 0) {
        throw new Error('Failed to generate PDF417 barcode array');
      }

      // Set canvas size based on barcode dimensions (matching backend settings)
      const moduleWidth = options.moduleWidth || 2.5;
      const moduleHeight = options.moduleHeight || 1;

      canvas.width = moduleWidth * barcodeArray.num_cols;
      canvas.height = moduleHeight * barcodeArray.num_rows;

      // Remove the style width/height settings that might cause scaling issues
      canvas.style.width = '';
      canvas.style.height = '';

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        throw new Error('Canvas 2D context unavailable');
      }

      // Clear the canvas first with white background
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw the barcode exactly like backend implementation
      let y = 0;
      for (let r = 0; r < barcodeArray.num_rows; r++) {
        let x = 0;
        for (let c = 0; c < barcodeArray.num_cols; c++) {
          if (barcodeArray.bcode[r][c] == 1) {
            ctx.fillStyle = '#000000';
            ctx.fillRect(x, y, moduleWidth, moduleHeight);
          }
          // Don't draw white pixels explicitly since we cleared with white
          x += moduleWidth;
        }
        y += moduleHeight;
      }

      barcodeReady.value = true;
      return {
        width: canvas.width,
        height: canvas.height,
        rows: barcodeArray.num_rows,
        cols: barcodeArray.num_cols,
      };
    } catch (error) {
      barcodeReady.value = false;
      throw error;
    }
  }

  return {
    barcodeReady,
    ensurePdf417Ready,
    drawPdf417,
  };
}
