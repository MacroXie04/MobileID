import { ref } from 'vue';
import { passkeyRegisterOptions, passkeyRegisterVerify } from '@shared/api/auth.js';
import { arrayBufferToB64url, b64urlToArrayBuffer } from '@auth/utils/passkey.js';

/**
 * Composable for handling passkey registration
 * @returns {Object} Passkey registration functions and state
 */
export function usePasskeyRegistration() {
  const passkeyBusy = ref(false);
  const error = ref(null);

  /**
   * Initiates passkey registration flow
   * @returns {Promise<boolean>} Success status
   */
  async function registerPasskey() {
    if (passkeyBusy.value) return false;

    passkeyBusy.value = true;
    error.value = null;

    try {
      // Get registration options from server
      const { success, publicKey, message } = await passkeyRegisterOptions();
      if (!success) {
        throw new Error(message || 'Failed to start passkey registration');
      }

      // Convert base64url-encoded challenge and user ID to ArrayBuffers
      const publicKeyOptions = { ...publicKey };
      publicKeyOptions.challenge = b64urlToArrayBuffer(publicKey.challenge);

      if (publicKey.user && publicKey.user.id != null) {
        publicKeyOptions.user = {
          ...publicKey.user,
          id: new Uint8Array(b64urlToArrayBuffer(publicKey.user.id)),
        };
      }

      // Ensure required user.displayName exists (browser requires it)
      if (publicKeyOptions.user && !publicKeyOptions.user.displayName) {
        publicKeyOptions.user.displayName = publicKeyOptions.user.name || 'User';
      }

      // Clean up problematic/experimental fields that browsers reject
      const cleanFields = ['hints', 'extensions'];
      cleanFields.forEach((field) => {
        if (publicKeyOptions[field] !== undefined) {
          delete publicKeyOptions[field];
        }
      });

      // Handle excluded credentials
      if (Array.isArray(publicKey.excludeCredentials)) {
        publicKeyOptions.excludeCredentials = publicKey.excludeCredentials.map((c) => ({
          ...c,
          id: b64urlToArrayBuffer(c.id),
        }));
      }

      // Request credential creation from authenticator
      const cred = await navigator.credentials.create({ publicKey: publicKeyOptions });
      if (!cred) {
        throw new Error('User aborted passkey registration');
      }

      // Convert ArrayBuffers back to base64url for server verification
      const attestation = {
        id: cred.id,
        type: cred.type,
        rawId: arrayBufferToB64url(cred.rawId),
        response: {
          clientDataJSON: arrayBufferToB64url(cred.response.clientDataJSON),
          attestationObject: arrayBufferToB64url(cred.response.attestationObject),
        },
      };

      // Verify credential with server
      const verifyRes = await passkeyRegisterVerify(attestation);
      if (!verifyRes.success) {
        error.value = verifyRes.message || 'Passkey registration failed';
        return false;
      }

      return true;
    } catch (e) {
      console.error('Passkey registration error:', e);
      error.value = e.message || 'Passkey registration failed';
      return false;
    } finally {
      passkeyBusy.value = false;
    }
  }

  return {
    passkeyBusy,
    error,
    registerPasskey,
  };
}
