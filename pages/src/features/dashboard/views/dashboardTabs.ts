// Typed metadata that drives the dashboard's navigation chrome (desktop rail +
// mobile tab bar). The shell renders the six tab bodies as explicit components
// (each has a distinct prop/emit surface), so this metadata only needs to carry
// what the navigation needs: a stable id, a label, and a Material icon.
//
// The ids are the canonical `?tab=` query values and must stay in sync with the
// allow-list in useDashboardLogic.ts and the v-show panes in the shell.

export type DashboardTabId = 'Overview' | 'Profile' | 'Camera' | 'Barcodes' | 'Devices' | 'Add';

export interface DashboardTab {
  id: DashboardTabId;
  label: string;
  icon: string;
}

export const DASHBOARD_TABS: readonly DashboardTab[] = [
  { id: 'Overview', label: 'Overview', icon: 'tune' },
  { id: 'Profile', label: 'Profile', icon: 'account_circle' },
  { id: 'Camera', label: 'Scanner Detection', icon: 'sensors' },
  { id: 'Barcodes', label: 'Available Barcodes', icon: 'inventory_2' },
  { id: 'Devices', label: 'Devices Management', icon: 'devices' },
  { id: 'Add', label: 'Add Barcode', icon: 'add_circle' },
];

export const DASHBOARD_TAB_IDS: readonly DashboardTabId[] = DASHBOARD_TABS.map((tab) => tab.id);
