import {getCookie} from '@/utils/auth/cookie';
import {useToken} from '@/composables/auth/useToken';
import {baseURL} from '@/config'

export function useApi() {
    const {checkAuthenticationError, refreshToken, handleTokenExpired} = useToken();

    /**
     * Make API calls with automatic token refresh on authentication errors
     */
    async function apiCallWithAutoRefresh(url, options = {}, retryCount = 0) {
        // Maximum number of retries, 1 time
        const maxRetries = 1;
        const controller = new AbortController();
        const timeoutMs = options.timeoutMs ?? 10000;
        const id = setTimeout(() => controller.abort('timeout'), timeoutMs);

        try {
            const res = await fetch(url, {
                credentials: "include",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/json",
                    ...options.headers
                },
                signal: controller.signal,
                ...options
            });
            clearTimeout(id);

            // Try parse JSON safely
            let data = null;
            const ct = res.headers?.get('content-type') || '';
            if (ct.includes('application/json')) {
                try {
                    data = await res.json();
                } catch (_) {
                    data = null;
                }
            }

            if (import.meta.env?.MODE !== 'production') {
                // Avoid logging sensitive payloads; show status only in dev.
                console.debug(`API ${res.status} ${url}`);
            }

            // Check if it is an authentication error
            if (checkAuthenticationError(data, res)) {
                console.log(`Token expired (retry count: ${retryCount}/${maxRetries})`);

                if (retryCount < maxRetries) {
                    console.log("Trying to refresh token and retry...");

                    // try to refresh token
                    const refreshSuccess = await refreshToken();

                    if (refreshSuccess) {
                        console.log("Token refreshed successfully, retrying...");
                        // Recursive call, increase retry count
                        return await apiCallWithAutoRefresh(url, options, retryCount + 1);
                    } else {
                        console.log("Token refresh failed, trying handleTokenExpired...");
                        const tokenRecoverySuccess = await handleTokenExpired();
                        if (tokenRecoverySuccess) {
                            console.log("Token recovery successful, retrying request");
                            return await apiCallWithAutoRefresh(url, options, retryCount + 1);
                        } else {
                            throw new Error("Token refresh failed");
                        }
                    }
                } else {
                    console.log("Maximum retries reached, trying final token recovery...");
                    const tokenRecoverySuccess = await handleTokenExpired();
                    if (tokenRecoverySuccess) {
                        console.log("Final token recovery successful, retrying request");
                        return await apiCallWithAutoRefresh(url, options, retryCount + 1);
                    } else {
                        throw new Error("Max retries exceeded");
                    }
                }
            }

            if (!res.ok) {
                // Create error with full response data for better error handling
                const error = new Error(`API call failed: ${res.status} - ${data?.detail || data?.message || 'Unknown error'}`);
                error.status = res.status;
                error.errors = data?.errors;
                error.responseData = data;
                throw error;
            }
            return data;

        } catch (error) {
            if (error?.name === 'AbortError' || error === 'timeout') {
                throw new Error('Network error: request_timeout');
            }
            if (typeof error?.message === 'string' && (error.message.includes("Token") || error.message.includes("retries"))) {
                throw error; // re-throw authentication related errors
            }
            if (import.meta.env?.MODE !== 'production') {
                console.error(`API request failed (${url}):`, error);
            }
            throw new Error(`Network error: ${error?.message || 'unknown_error'}`);
        }
    }

    /**
     * Generate barcode API call
     */
    async function apiGenerateBarcode() {
        return await apiCallWithAutoRefresh(`${baseURL}/generate_barcode/`, {
            method: "POST"
        });
    }

    /**
     * Get active profile info based on user settings
     */
    async function apiGetActiveProfile() {
        return await apiCallWithAutoRefresh(`${baseURL}/active_profile/`, {
            method: "GET"
        });
    }

    /**
     * Barcode Dashboard API calls
     */
    async function apiGetBarcodeDashboard() {
        return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
            method: "GET"
        });
    }

    async function apiUpdateBarcodeSettings(settings) {
        return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
            method: "POST",
            body: JSON.stringify(settings)
        });
    }

    async function apiCreateBarcode(barcode) {
        return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
            method: "PUT",
            body: JSON.stringify({barcode})
        });
    }

    async function apiDeleteBarcode(barcodeId) {
        return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
            method: "DELETE",
            body: JSON.stringify({barcode_id: barcodeId})
        });
    }

    async function apiUpdateBarcodeShare(barcodeId, share) {
        return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
            method: "PATCH",
            body: JSON.stringify({
                barcode_id: barcodeId,
                share_with_others: !!share
            })
        });
    }

    async function apiUpdateBarcodeDailyLimit(barcodeId, dailyLimit) {
        return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
            method: "PATCH",
            body: JSON.stringify({
                barcode_id: barcodeId,
                daily_usage_limit: dailyLimit
            })
        });
    }

    /**
     * Transfer CatCard API call
     */
    async function apiTransferCatCard(cookies) {
        return await apiCallWithAutoRefresh(`${baseURL}/transfer/`, {
            method: "POST",
            body: JSON.stringify({
                cookies: cookies,
                page: 'https://icatcard.ucmerced.edu/mobileid/',
                ts: Date.now()
            })
        });
    }

    return {
        apiCallWithAutoRefresh,
        apiGenerateBarcode,
        apiGetActiveProfile,
        apiGetBarcodeDashboard,
        apiUpdateBarcodeSettings,
        apiCreateBarcode,
        apiDeleteBarcode,
        apiTransferCatCard,
        apiUpdateBarcodeShare,
        apiUpdateBarcodeDailyLimit
    };
} 