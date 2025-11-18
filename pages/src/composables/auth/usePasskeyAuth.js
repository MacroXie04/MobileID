import {ref} from 'vue';
import {passkeyAuthOptions, passkeyAuthVerify} from '@/api/auth.js';
import {arrayBufferToB64url, b64urlToArrayBuffer} from '@/utils/auth/passkey.js';

/**
 * Composable for handling passkey authentication
 * @returns {Object} Passkey authentication functions and state
 */
export function usePasskeyAuth() {
    const passkeyBusy = ref(false);
    const error = ref(null);

    /**
     * Initiates passkey sign-in flow
     * @param {string} username - Optional username for passkey authentication
     * @returns {Promise<boolean>} Success status
     */
    async function signInWithPasskey(username) {
        if (passkeyBusy.value) return false;

        passkeyBusy.value = true;
        error.value = null;

        try {
            // Get authentication options from server
            const {success, publicKey, message} = await passkeyAuthOptions(username || undefined);
            if (!success) {
                throw new Error(message || 'Failed to start passkey auth');
            }

            // Convert base64url-encoded challenge and credential IDs to ArrayBuffers
            const requestOptions = {...publicKey};
            requestOptions.challenge = b64urlToArrayBuffer(publicKey.challenge);
            if (Array.isArray(publicKey.allowCredentials)) {
                requestOptions.allowCredentials = publicKey.allowCredentials.map(c => ({
                    ...c,
                    id: b64urlToArrayBuffer(c.id)
                }));
            }

            // Request credential from authenticator
            const assertion = await navigator.credentials.get({publicKey: requestOptions});
            if (!assertion) {
                throw new Error('User aborted passkey authentication');
            }

            // Convert ArrayBuffers back to base64url for server verification
            const credential = {
                id: assertion.id,
                type: assertion.type,
                rawId: arrayBufferToB64url(assertion.rawId),
                response: {
                    clientDataJSON: arrayBufferToB64url(assertion.response.clientDataJSON),
                    authenticatorData: arrayBufferToB64url(assertion.response.authenticatorData),
                    signature: arrayBufferToB64url(assertion.response.signature),
                    userHandle: assertion.response.userHandle
                        ? arrayBufferToB64url(assertion.response.userHandle)
                        : null,
                },
            };

            // Verify credential with server
            const verifyRes = await passkeyAuthVerify(credential);
            if (verifyRes.success) {
                return true;
            } else {
                error.value = verifyRes.message || 'Passkey sign-in failed';
                return false;
            }
        } catch (e) {
            console.error('Passkey sign-in error:', e);
            error.value = e.message || 'Passkey sign-in failed';
            return false;
        } finally {
            passkeyBusy.value = false;
        }
    }

    return {
        passkeyBusy,
        error,
        signInWithPasskey,
    };
}
