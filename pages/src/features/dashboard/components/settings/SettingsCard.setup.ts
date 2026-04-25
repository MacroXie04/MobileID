import { computed } from 'vue';
import type { PropType } from 'vue';
import type { Barcode, BarcodeChoice, BarcodeSettings, PullSettings } from '@barcode';

// CSS - use shared dashboard styles
import '@dashboard/styles/BarcodeDashboard.css';

export const propsDefinition = {
  isSaving: { type: Boolean, default: false },
  currentBarcodeInfo: { type: String, default: '' },
  selectedBarcode: { type: Object as PropType<Barcode | null>, default: null },
  barcodeChoices: { type: Array as PropType<BarcodeChoice[]>, default: () => [] },
  settings: { type: Object as PropType<BarcodeSettings>, default: () => ({}) },
  pullSettings: {
    type: Object as PropType<PullSettings>,
    default: () => ({ pull_setting: 'Disable', gender_setting: 'Unknow' }),
  },
  isDynamicSelected: { type: Boolean, default: false },
  currentBarcodeHasProfile: { type: Boolean, default: false },
  errors: { type: Object as PropType<Record<string, string>>, default: () => ({}) },
  associateUserProfileWithBarcode: { type: Boolean, default: false },
  formatRelativeTime: { type: Function, required: true },
  formatDate: { type: Function, required: true },
};

export const emitsDefinition = ['update-associate', 'update-pull-setting', 'update-gender-setting'];

export function useSettingsCardSetup(args: any = {}) {
  const { props } = args;
  const componentProps = props ?? {};

  const hasErrors = computed(() => Object.keys(componentProps.errors || {}).length > 0);

  const activeIcon = computed(() => {
    const id = componentProps.settings?.barcode || null;
    const current = (componentProps.barcodeChoices || []).find((c) => c.id === id);
    if (!current) return 'barcode';
    if (current.barcode_type === 'DynamicBarcode') return 'qr_code_2';
    return 'barcode';
  });

  return { hasErrors, activeIcon };
}
