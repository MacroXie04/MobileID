import { useBarcodesListLogic } from '@dashboard/composables/useBarcodesListLogic';
import type { PropType } from 'vue';
import type { Barcode, BarcodeSettings, PullSettings } from '@barcode';

// CSS - use shared dashboard styles
import '@dashboard/styles/BarcodeDashboard.css';

export const emitsDefinition = [
  'update-filter',
  'toggle-owned',
  'set-active',
  'toggle-share',
  'delete',
  'update-limit',
  'increment-limit',
  'decrement-limit',
  'toggle-unlimited-switch',
  'apply-limit-preset',
];

export const propsDefinition = {
  activeTab: { type: String, default: 'Barcodes' },
  settings: { type: Object as PropType<BarcodeSettings>, required: true },
  pullSettings: {
    type: Object as PropType<PullSettings>,
    default: () => ({ pull_setting: 'Disable', gender_setting: 'Unknow' }),
  },
  filteredBarcodes: { type: Array as PropType<Barcode[]>, default: () => [] },
  hasActiveFilters: { type: Boolean, default: false },
  filterType: { type: String, default: 'All' },
  ownedOnly: { type: Boolean, default: false },
  updatingLimit: { type: Object as PropType<Record<string, boolean>>, default: () => ({}) },
};

export function useBarcodesListCardSetup() {
  return useBarcodesListLogic();
}
