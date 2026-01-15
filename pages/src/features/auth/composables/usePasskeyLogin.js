import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { passkeyAuthOptions, passkeyAuthVerify, userInfo } from '@shared/api/auth.js';
import { ApiError } from '@shared/api/client.js';
import {
  isWebAuthnSupported,
  preparePublicKeyOptions,
  serializeCredential,
} from '@shared/utils/webauthn.js';

/**
 * Composable for handling passkey-based authentication
 */
export function usePasskeyLogin() {
  const router = useRouter();
  const passkeyLoading = ref(false);
  const passkeyError = ref('');
  const passkeySupported = ref(isWebAuthnSupported());

  /**
   * Handle passkey login flow
   */
  async function handlePasskeyLogin() {
    if (!passkeySupported.value) {
      passkeyError.value = 'Passkeys are not supported in this browser.';
      return;
    }

    passkeyLoading.value = true;
    passkeyError.value = '';

    try {
      // Step 1: Get authentication options from server
      const optionsResponse = await passkeyAuthOptions();

      if (!optionsResponse.success || !optionsResponse.publicKey) {
        throw new Error('Failed to get authentication options');
      }

      // Step 2: Prepare options for WebAuthn API
      const publicKeyOptions = preparePublicKeyOptions(optionsResponse.publicKey);

      // Step 3: Call WebAuthn API to get credential
      const credential = await navigator.credentials.get({
        publicKey: publicKeyOptions,
      });

      if (!credential) {
        throw new Error('No credential received from authenticator');
      }

      // Step 4: Serialize and send credential to server for verification
      const serializedCredential = serializeCredential(credential);
      const verifyResponse = await passkeyAuthVerify(serializedCredential);

      if (verifyResponse.success && verifyResponse.message === 'Login successful') {
        // Step 5: Verify session and redirect
        const user = await userInfo();
        if (user) {
          window.userInfo = user;
          await router.push('/');
        } else {
          passkeyError.value =
            'Login successful but session could not be established. Please check your cookie settings.';
        }
      } else {
        passkeyError.value = 'Passkey authentication failed. Please try again.';
      }
    } catch (err) {
      console.error('Passkey login error:', err);

      if (err.name === 'NotAllowedError') {
        passkeyError.value = 'Authentication was cancelled or not allowed.';
      } else if (err.name === 'SecurityError') {
        passkeyError.value =
          'Security error during authentication. Please ensure you are on a secure connection.';
      } else if (err.name === 'NotSupportedError') {
        passkeyError.value = 'Passkeys are not supported on this device.';
      } else if (err instanceof ApiError) {
        passkeyError.value = err.data?.message || err.data?.detail || 'Authentication failed.';
      } else {
        passkeyError.value = err.message || 'Passkey authentication failed. Please try again.';
      }
    } finally {
      passkeyLoading.value = false;
    }
  }

  /**
   * Clear passkey error message
   */
  function clearPasskeyError() {
    passkeyError.value = '';
  }

  return {
    passkeyLoading,
    passkeyError,
    passkeySupported,
    handlePasskeyLogin,
    clearPasskeyError,
  };
}
