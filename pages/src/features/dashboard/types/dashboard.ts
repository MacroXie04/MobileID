import type { Barcode, BarcodeChoice, BarcodeSettings, PullSettings } from '@barcode';

export interface AddBarcodeEmit {
  (event: 'message', text: string | undefined, severity: 'success' | 'danger'): void;
  (event: 'added'): void;
}

export interface Device {
  id: number;
  jti?: string;
  device_name: string;
  browser?: string;
  os?: string;
  device_type: string;
  ip_address?: string | null;
  user_agent?: string;
  created_at: string;
  expires_at: string;
  last_active?: string | null;
  is_current: boolean;
}

export interface DevicesListResponse {
  devices?: Device[];
  count?: number;
}

export interface DashboardSettings {
  associate_user_profile_with_barcode: boolean;
  scanner_detection_enabled: boolean;
  prefer_front_camera: boolean;
  barcode: string | number | null;
}

export interface SettingsCardProps {
  isSaving?: boolean;
  currentBarcodeInfo?: string;
  selectedBarcode?: Barcode | null;
  barcodeChoices?: BarcodeChoice[];
  settings?: BarcodeSettings;
  pullSettings?: PullSettings;
  isDynamicSelected?: boolean;
  currentBarcodeHasProfile?: boolean;
  errors?: Record<string, string>;
  associateUserProfileWithBarcode?: boolean;
  formatRelativeTime?: (value: string) => string;
  formatDate?: (value: string) => string;
}

export interface SettingsCardSetupArgs {
  props?: SettingsCardProps;
}
