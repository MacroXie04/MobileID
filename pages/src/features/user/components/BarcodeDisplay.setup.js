import '@material/web/button/elevated-button.js';
import '@material/web/icon/icon.js';
import '@material/web/progress/circular-progress.js';
import '@material/web/progress/linear-progress.js';
import '@material/web/ripple/ripple.js';

import { useBarcodeDisplay } from '@dashboard/composables/barcode/useBarcodeDisplay.js';
import { usePdf417 } from '@dashboard/composables/barcode/usePdf417.js';

// CSS
import '@/assets/styles/user/user-merged.css';

export const emitsDefinition = ['generate'];

export function useUserBarcodeDisplaySetup({ emit } = {}) {
  const emitFn = emit ?? (() => {});

  // Use composables
  const {
    isProcessing,
    successMessage,
    errorMessage,
    barcodeDisplayed,
    buttonMessage,
    progressValue,
    showProgressBar,
    buttonIcon,
    clearBarcodeContainer,
    resetUI,
    startProcessing,
    showSuccess,
    showError,
  } = useBarcodeDisplay();

  const { drawPdf417ToContainer } = usePdf417();

  // Handle generate button click
  function handleGenerate() {
    if (isProcessing.value) return;
    emitFn('generate');
  }

  // Draw PDF417 barcode
  function drawPDF417(data) {
    drawPdf417ToContainer('barcode-container', data, {
      moduleWidth: 2.5,
      moduleHeight: 1,
    });
  }

  const exposeBindings = {
    startProcessing,
    showSuccess,
    showError,
    drawPDF417,
    resetUI,
  };

  return {
    isProcessing,
    successMessage,
    errorMessage,
    barcodeDisplayed,
    buttonMessage,
    progressValue,
    showProgressBar,
    buttonIcon,
    clearBarcodeContainer,
    handleGenerate,
    exposeBindings,
  };
}
