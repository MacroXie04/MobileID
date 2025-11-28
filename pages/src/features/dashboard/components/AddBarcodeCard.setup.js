import { useAddBarcodeLogic } from '@dashboard/composables/useAddBarcodeLogic.js';

// CSS - use shared dashboard styles
import '@/assets/styles/dashboard/BarcodeDashboard.css';

export const emitsDefinition = ['added', 'message'];

export const propsDefinition = {
  activeTab: { type: String, default: 'Add' },
};

export function useAddBarcodeCardSetup({ emit } = {}) {
  return useAddBarcodeLogic(emit);
}
