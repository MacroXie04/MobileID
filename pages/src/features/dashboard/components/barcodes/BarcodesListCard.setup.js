import { useBarcodesListLogic } from '@dashboard/composables/useBarcodesListLogic.js';

// CSS - use shared dashboard styles
import '@/assets/styles/dashboard/BarcodeDashboard.css';

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
  settings: { type: Object, required: true },
  pullSettings: {
    type: Object,
    default: () => ({ pull_setting: 'Disable', gender_setting: 'Unknow' }),
  },
  filteredBarcodes: { type: Array, default: () => [] },
  hasActiveFilters: { type: Boolean, default: false },
  filterType: { type: String, default: 'All' },
  ownedOnly: { type: Boolean, default: false },
  updatingLimit: { type: Object, default: () => ({}) },
};

export function useBarcodesListCardSetup() {
  return useBarcodesListLogic();
}
