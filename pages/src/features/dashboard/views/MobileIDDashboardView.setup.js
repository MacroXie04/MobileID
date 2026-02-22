import { useRouter } from 'vue-router';
import { formatDate, formatRelativeTime } from '@shared/utils/common/dateUtils';
import SettingsCard from '@dashboard/components/settings/SettingsCard.vue';
import CameraSettingsCard from '@dashboard/components/settings/CameraSettingsCard.vue';
import BarcodesListCard from '@dashboard/components/barcodes/BarcodesListCard.vue';
import AddBarcodeCard from '@dashboard/components/barcodes/AddBarcodeCard.vue';
import DevicesCard from '@dashboard/components/devices/DevicesCard.vue';
import ProfileTabCard from '@dashboard/components/profile/ProfileTabCard.vue';
import { useDashboardLogic } from '@dashboard/composables/useDashboardLogic.js';
import '@/assets/styles/dashboard/BarcodeDashboard.css';

export {
  SettingsCard,
  CameraSettingsCard,
  BarcodesListCard,
  AddBarcodeCard,
  DevicesCard,
  ProfileTabCard,
};

export function useBarcodeDashboardViewSetup() {
  const router = useRouter();

  return {
    router,
    formatDate,
    formatRelativeTime,
    ...useDashboardLogic(),
  };
}
