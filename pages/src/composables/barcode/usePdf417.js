import { ref } from 'vue';

export function usePdf417() {
  const barcodeReady = ref(false);

  /**
   * Draw PDF417 barcode on canvas element
   * @param {HTMLCanvasElement} canvas - The canvas element to draw on
   * @param {string} text - The text to encode in the barcode
   */
  function drawPdf417(canvas, text) {
    if (!canvas) {
      console.error('Canvas element not found');
      return;
    }

    console.log('Generating barcode for text:', text);

    // Check if global PDF417 object is available
    if (typeof window.PDF417 === 'undefined') {
      console.error('PDF417 library not loaded');
      return;
    }

    try {
      // Initialize PDF417 with the barcode text
      window.PDF417.init(text);
      const barcodeArray = window.PDF417.getBarcodeArray();

      if (!barcodeArray || !barcodeArray.bcode || barcodeArray.num_rows <= 0) {
        console.error('Failed to generate PDF417 barcode array');
        return;
      }

      console.log('Barcode array generated:', {
        rows: barcodeArray.num_rows,
        cols: barcodeArray.num_cols,
      });

      // Set canvas size based on barcode dimensions (matching backend settings)
      const moduleWidth = 2.5;
      const moduleHeight = 1;

      canvas.width = moduleWidth * barcodeArray.num_cols;
      canvas.height = moduleHeight * barcodeArray.num_rows;

      // Remove the style width/height settings that might cause scaling issues
      canvas.style.width = '';
      canvas.style.height = '';

      const ctx = canvas.getContext('2d');

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

      console.log('PDF417 barcode rendered successfully');
      barcodeReady.value = true;
    } catch (error) {
      console.error('PDF417 generation failed:', error);
      barcodeReady.value = false;
    }
  }

  return {
    barcodeReady,
    drawPdf417,
  };
}
