import { baseURL } from '@shared/config/config';
import { useAuthenticatedRequest } from '@auth';
import type {
  BarcodeDashboardPayload,
  BarcodeShareResponse,
  BarcodeSettings,
  CreateDynamicBarcodePayload,
  GenerateBarcodeResponse,
  TransferDynamicBarcodeResponse,
} from '@barcode/types/barcode';

export function useBarcodeApi() {
  const { apiCallWithAutoRefresh } = useAuthenticatedRequest();

  async function apiGenerateBarcode() {
    return apiCallWithAutoRefresh<GenerateBarcodeResponse>(`${baseURL}/generate_barcode/`, {
      method: 'POST',
    });
  }

  async function apiGetActiveProfile() {
    return apiCallWithAutoRefresh<{ profile_info?: Record<string, string> }>(
      `${baseURL}/active_profile/`,
      {
        method: 'GET',
      }
    );
  }

  async function apiGetBarcodeDashboard() {
    return apiCallWithAutoRefresh<BarcodeDashboardPayload>(`${baseURL}/barcode_dashboard/`, {
      method: 'GET',
    });
  }

  async function apiUpdateBarcodeSettings(settings: BarcodeSettings) {
    return apiCallWithAutoRefresh<BarcodeDashboardPayload & { status?: string }>(
      `${baseURL}/barcode_dashboard/`,
      {
        method: 'POST',
        body: JSON.stringify(settings),
      }
    );
  }

  async function apiCreateBarcode(barcode: string) {
    return apiCallWithAutoRefresh<{ status?: string; message?: string }>(
      `${baseURL}/barcode_dashboard/`,
      {
        method: 'PUT',
        body: JSON.stringify({ barcode }),
      }
    );
  }

  async function apiDeleteBarcode(barcodeId: string | number) {
    return apiCallWithAutoRefresh<{ status?: string; message?: string }>(
      `${baseURL}/barcode_dashboard/`,
      {
        method: 'DELETE',
        body: JSON.stringify({ barcode_id: barcodeId }),
      }
    );
  }

  async function apiUpdateBarcodeShare(barcodeId: string | number, share: boolean) {
    return apiCallWithAutoRefresh<BarcodeShareResponse>(`${baseURL}/barcode_dashboard/`, {
      method: 'PATCH',
      body: JSON.stringify({
        barcode_id: barcodeId,
        share_with_others: !!share,
      }),
    });
  }

  async function apiUpdateBarcodeDailyLimit(barcodeId: string | number, dailyLimit: number | null) {
    return apiCallWithAutoRefresh<{ status?: string; message?: string }>(
      `${baseURL}/barcode_dashboard/`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          barcode_id: barcodeId,
          daily_usage_limit: dailyLimit,
        }),
      }
    );
  }

  async function apiCreateDynamicBarcodeWithProfile(data: CreateDynamicBarcodePayload) {
    return apiCallWithAutoRefresh<GenerateBarcodeResponse>(`${baseURL}/dynamic_barcode/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async function apiTransferDynamicBarcode(htmlContent: string) {
    return apiCallWithAutoRefresh<TransferDynamicBarcodeResponse>(
      `${baseURL}/transfer_dynamic_barcode/`,
      {
        method: 'POST',
        body: JSON.stringify({ html: htmlContent }),
      }
    );
  }

  return {
    apiGenerateBarcode,
    apiGetActiveProfile,
    apiGetBarcodeDashboard,
    apiUpdateBarcodeSettings,
    apiCreateBarcode,
    apiDeleteBarcode,
    apiUpdateBarcodeShare,
    apiUpdateBarcodeDailyLimit,
    apiCreateDynamicBarcodeWithProfile,
    apiTransferDynamicBarcode,
  };
}
