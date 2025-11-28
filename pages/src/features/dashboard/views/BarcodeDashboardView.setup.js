import { useRouter } from 'vue-router';
import { formatDate, formatRelativeTime } from '@shared/utils/common/dateUtils';
import SettingsCard from '@dashboard/components/SettingsCard.vue';
import CameraSettingsCard from '@dashboard/components/CameraSettingsCard.vue';
import BarcodesListCard from '@dashboard/components/BarcodesListCard.vue';
import AddBarcodeCard from '@dashboard/components/AddBarcodeCard.vue';
import DevicesCard from '@dashboard/components/DevicesCard.vue';
import { useDashboardLogic } from '@dashboard/composables/useDashboardLogic.js';
import '@/assets/styles/dashboard/BarcodeDashboard.css';

export { SettingsCard, CameraSettingsCard, BarcodesListCard, AddBarcodeCard, DevicesCard };

export function useBarcodeDashboardViewSetup() {
  const router = useRouter();

  return {
    router,
    formatDate,
    formatRelativeTime,
    ...useDashboardLogic(),
  };
}
