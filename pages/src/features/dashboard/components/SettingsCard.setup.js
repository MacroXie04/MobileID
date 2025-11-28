import { computed } from 'vue';

// CSS - use shared dashboard styles
import '@/assets/styles/dashboard/BarcodeDashboard.css';

export const propsDefinition = {
  isSaving: { type: Boolean, default: false },
  currentBarcodeInfo: { type: String, default: '' },
  selectedBarcode: { type: Object, default: null },
  barcodeChoices: { type: Array, default: () => [] },
  settings: { type: Object, default: () => ({}) },
  pullSettings: {
    type: Object,
    default: () => ({ pull_setting: 'Disable', gender_setting: 'Unknow' }),
  },
  isUserGroup: { type: Boolean, default: false },
  isDynamicSelected: { type: Boolean, default: false },
  currentBarcodeHasProfile: { type: Boolean, default: false },
  errors: { type: Object, default: () => ({}) },
  associateUserProfileWithBarcode: { type: Boolean, default: false },
  serverVerification: { type: Boolean, default: false },
  formatRelativeTime: { type: Function, required: true },
  formatDate: { type: Function, required: true },
};

export const emitsDefinition = [
  'update-associate',
  'update-server',
  'update-pull-setting',
  'update-gender-setting',
];

export function useSettingsCardSetup({ props } = {}) {
  const componentProps = props ?? {};

  const hasErrors = computed(() => Object.keys(componentProps.errors || {}).length > 0);

  const activeIcon = computed(() => {
    const id = componentProps.settings?.barcode ? Number(componentProps.settings.barcode) : null;
    const current = (componentProps.barcodeChoices || []).find((c) => Number(c.id) === id);
    if (!current) return 'barcode';
    if (current.barcode_type === 'DynamicBarcode') return 'qr_code_2';
    if (current.barcode_type === 'Identification') return 'badge';
    return 'barcode';
  });

  return { hasErrors, activeIcon };
}
