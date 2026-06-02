import { useAddBarcodeLogic } from '@dashboard/composables/useAddBarcodeLogic';
import type { AddBarcodeEmit } from '@dashboard/types/dashboard';

// CSS - use shared dashboard styles
import '@dashboard/styles/BarcodeDashboard.css';

export const emitsDefinition = ['added', 'message'];

export const propsDefinition = {
  activeTab: { type: String, default: 'Add' },
};

export interface AddBarcodeCardSetupArgs {
  emit?: AddBarcodeEmit;
}

export function useAddBarcodeCardSetup(args: AddBarcodeCardSetupArgs = {}) {
  const { emit } = args;
  return useAddBarcodeLogic(emit);
}
