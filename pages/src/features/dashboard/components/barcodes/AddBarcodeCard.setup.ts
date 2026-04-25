import { useAddBarcodeLogic } from '@dashboard/composables/useAddBarcodeLogic';

// CSS - use shared dashboard styles
import '@dashboard/styles/BarcodeDashboard.css';

export const emitsDefinition = ['added', 'message'];

export const propsDefinition = {
  activeTab: { type: String, default: 'Add' },
};

export function useAddBarcodeCardSetup(args: any = {}) {
  const { emit } = args;
  return useAddBarcodeLogic(emit);
}
