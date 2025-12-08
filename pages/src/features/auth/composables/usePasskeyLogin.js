import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { passkeyAuthOptions, passkeyAuthVerify, userInfo } from '@shared/api/auth.js';
import { ApiError } from '@shared/api/client.js';

/**
 * Composable for handling passkey-based authentication
 */
export function usePasskeyLogin() {
  const router = useRouter();
  const passkeyLoading = ref(false);
  const passkeyError = ref('');
  const passkeySupported = ref(isWebAuthnSupported());

  /**
   * Check if WebAuthn is supported in this browser
   */
  function isWebAuthnSupported() {
    return !!(
      window.PublicKeyCredential &&
      typeof window.PublicKeyCredential === 'function' &&
      navigator.credentials &&
      typeof navigator.credentials.get === 'function'
    );
  }

  /**
   * Convert a base64url string to an ArrayBuffer
   */
  function base64urlToBuffer(base64url) {
    // Replace URL-safe chars with standard base64 chars
    const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    // Add padding if needed
    const padLen = (4 - (base64.length % 4)) % 4;
    const padded = base64 + '='.repeat(padLen);
    const binary = atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * Convert an ArrayBuffer to a base64url string
   */
  function bufferToBase64url(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    const base64 = btoa(binary);
    // Convert to base64url
    return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  /**
   * Prepare publicKey options for navigator.credentials.get
   */
  function preparePublicKeyOptions(publicKey) {
    const options = { ...publicKey };

    // Convert challenge from base64url to ArrayBuffer
    if (typeof options.challenge === 'string') {
      options.challenge = base64urlToBuffer(options.challenge);
    }

    // Convert allowCredentials ids from base64url to ArrayBuffer
    if (options.allowCredentials) {
      options.allowCredentials = options.allowCredentials.map((cred) => ({
        ...cred,
        id: typeof cred.id === 'string' ? base64urlToBuffer(cred.id) : cred.id,
      }));
    }

    return options;
  }

  /**
   * Serialize credential for sending to server
   */
  function serializeCredential(credential) {
    const response = credential.response;

    return {
      id: credential.id,
      rawId: bufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        clientDataJSON: bufferToBase64url(response.clientDataJSON),
        authenticatorData: bufferToBase64url(response.authenticatorData),
        signature: bufferToBase64url(response.signature),
        userHandle: response.userHandle ? bufferToBase64url(response.userHandle) : null,
      },
    };
  }

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
        passkeyError.value = 'Security error during authentication. Please ensure you are on a secure connection.';
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
