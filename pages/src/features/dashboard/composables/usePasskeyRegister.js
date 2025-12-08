import { onMounted, ref } from 'vue';
import { passkeyRegisterOptions, passkeyRegisterVerify, getUserProfile } from '@shared/api/auth.js';
import { ApiError } from '@shared/api/client.js';

export function usePasskeyRegister() {
  const passkeySupported = ref(isWebAuthnSupported());
  const passkeyLoading = ref(false);
  const passkeyError = ref('');
  const passkeySuccess = ref('');
  const hasPasskey = ref(false);

  function isWebAuthnSupported() {
    return !!(
      typeof window !== 'undefined' &&
      window.PublicKeyCredential &&
      typeof window.PublicKeyCredential === 'function' &&
      navigator.credentials &&
      typeof navigator.credentials.create === 'function'
    );
  }

  function base64urlToBuffer(base64url) {
    const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    const padLen = (4 - (base64.length % 4)) % 4;
    const padded = base64 + '='.repeat(padLen);
    const binary = atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  function bufferToBase64url(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    const base64 = btoa(binary);
    return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  function prepareRegistrationOptions(publicKey) {
    const options = { ...publicKey };

    if (typeof options.challenge === 'string') {
      options.challenge = base64urlToBuffer(options.challenge);
    }

    if (options.user && typeof options.user.id === 'string') {
      options.user = { ...options.user, id: base64urlToBuffer(options.user.id) };
    }

    if (options.excludeCredentials) {
      options.excludeCredentials = options.excludeCredentials.map((cred) => ({
        ...cred,
        id: typeof cred.id === 'string' ? base64urlToBuffer(cred.id) : cred.id,
      }));
    }

    return options;
  }

  function serializeRegistrationCredential(credential) {
    const response = credential.response;

    return {
      id: credential.id,
      rawId: bufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        attestationObject: bufferToBase64url(response.attestationObject),
        clientDataJSON: bufferToBase64url(response.clientDataJSON),
      },
    };
  }

  async function registerPasskey() {
    if (!passkeySupported.value) {
      passkeyError.value = 'Passkeys are not supported in this browser.';
      passkeySuccess.value = '';
      return false;
    }

    passkeyLoading.value = true;
    passkeyError.value = '';
    passkeySuccess.value = '';

    try {
      const optionsResponse = await passkeyRegisterOptions();
      if (!optionsResponse.success || !optionsResponse.publicKey) {
        throw new Error('Failed to get registration options');
      }

      const publicKeyOptions = prepareRegistrationOptions(optionsResponse.publicKey);
      const credential = await navigator.credentials.create({ publicKey: publicKeyOptions });

      if (!credential) {
        throw new Error('No credential returned from authenticator');
      }

      const serializedCredential = serializeRegistrationCredential(credential);
      const verifyResponse = await passkeyRegisterVerify(serializedCredential);

      if (verifyResponse.success) {
        passkeySuccess.value = 'Passkey registered successfully.';
        hasPasskey.value = true;
        // Refresh server state (best-effort)
        fetchPasskeyStatus();
        return true;
      } else {
        passkeyError.value = verifyResponse.message || 'Passkey registration failed.';
        return false;
      }
    } catch (err) {
      console.error('Passkey registration error:', err);

      if (err.name === 'NotAllowedError') {
        passkeyError.value = 'Registration was cancelled or not allowed.';
      } else if (err.name === 'SecurityError') {
        passkeyError.value =
          'Security error during registration. Please ensure you are on a secure connection.';
      } else if (err.name === 'NotSupportedError') {
        passkeyError.value = 'Passkeys are not supported on this device.';
      } else if (err instanceof ApiError) {
        passkeyError.value = err.data?.message || err.data?.detail || 'Registration failed.';
      } else {
        passkeyError.value = err.message || 'Passkey registration failed. Please try again.';
      }
      return false;
    } finally {
      passkeyLoading.value = false;
    }
  }

  async function fetchPasskeyStatus() {
    try {
      const profile = await getUserProfile();
      if (profile?.data?.has_passkey !== undefined) {
        hasPasskey.value = Boolean(profile.data.has_passkey);
      }
    } catch (err) {
      // Non-fatal; surface as banner
      const message =
        err instanceof ApiError
          ? err.data?.detail || err.message
          : err?.message || 'Failed to load passkey status.';
      passkeyError.value = message;
    }
  }

  function clearPasskeyError() {
    passkeyError.value = '';
  }

  function clearPasskeySuccess() {
    passkeySuccess.value = '';
  }

  onMounted(() => {
    fetchPasskeyStatus();
  });

  return {
    passkeySupported,
    passkeyLoading,
    passkeyError,
    passkeySuccess,
    hasPasskey,
    fetchPasskeyStatus,
    registerPasskey,
    clearPasskeyError,
    clearPasskeySuccess,
  };
}
