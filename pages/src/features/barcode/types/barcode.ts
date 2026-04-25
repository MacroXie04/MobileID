export type BarcodeType = 'DynamicBarcode' | 'Others' | string;

export interface BarcodeProfileInfo {
  name?: string;
  information_id?: string;
  avatar_data?: string;
  has_avatar?: boolean;
}

export interface Barcode {
  id?: string | number;
  barcode_uuid?: string;
  barcode: string;
  barcode_type: BarcodeType;
  has_profile_addon?: boolean;
  is_owned_by_current_user?: boolean;
  share_with_others?: boolean;
  daily_usage_limit?: number | null;
  profile_info?: BarcodeProfileInfo;
  owner?: string;
  usage_count?: number;
  last_used?: string | null;
  usage_stats?: {
    today?: number;
    total?: number;
    daily_used?: number;
    daily_limit?: number;
    daily_remaining?: number;
    [key: string]: unknown;
  };
  recent_transactions?: Array<{
    id: string | number;
    user?: string;
    time_created: string;
  }>;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface BarcodeChoice {
  id: string | number;
  barcode: string;
  barcode_type: BarcodeType;
  has_profile_addon?: boolean;
}

export interface BarcodeSettings {
  associate_user_profile_with_barcode?: boolean;
  scanner_detection_enabled?: boolean;
  prefer_front_camera?: boolean;
  barcode?: string | number | null;
  pull_settings?: PullSettings;
}

export interface PullSettings {
  pull_setting?: string;
  gender_setting?: string;
}

export interface BarcodeDashboardPayload {
  status?: string;
  settings: BarcodeSettings & {
    barcode_choices?: BarcodeChoice[];
  };
  pull_settings?: PullSettings;
  barcodes?: Barcode[];
  message?: string;
}

export interface GenerateBarcodeResponse {
  status?: string;
  barcode?: string;
  message?: string;
  profile_info?: BarcodeProfileInfo;
}

export interface CreateDynamicBarcodePayload {
  barcode: string;
  name: string;
  information_id: string;
  gender: string;
  avatar?: string;
}

export interface TransferDynamicBarcodeResponse {
  status?: string;
  message?: string;
  errors?: Record<string, string | string[]>;
}

export interface BarcodeShareResponse {
  status?: string;
  message?: string;
  barcode?: Pick<Barcode, 'share_with_others'>;
}
