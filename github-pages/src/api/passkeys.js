import { baseURL } from '@/config';

// Helper to convert base64 to ArrayBuffer (handles both base64url and standard base64)
function base64ToArrayBuffer(base64) {
  // Check if it's standard base64 (has padding or +/)
  if (base64.includes('+') || base64.includes('/') || base64.includes('=')) {
    // Standard base64 - decode directly
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  } else {
    // base64url - convert to standard base64 first
    const base64std = base64.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64std + '=='.substring(0, (4 - base64std.length % 4) % 4);
    const binary = atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }
}

// Helper to convert ArrayBuffer to base64url
function arrayBufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary);
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

// Register a new passkey
export async function registerPasskey() {
  try {
    // 1. Get registration options from server
    const optionsResponse = await fetch(`${baseURL}/authn/passkeys/register/options/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'
    });
    
    if (!optionsResponse.ok) {
      throw new Error('Failed to get registration options');
    }
    
    const { options } = await optionsResponse.json();
    
    // 2. Convert options for WebAuthn API
    const publicKeyCredentialCreationOptions = {
      ...options,
      challenge: base64ToArrayBuffer(options.challenge),
      user: {
        ...options.user,
        id: base64ToArrayBuffer(options.user.id)
      },
      excludeCredentials: options.excludeCredentials?.map(cred => ({
        ...cred,
        id: base64ToArrayBuffer(cred.id)
      })) || []
    };
    
    // 3. Create credential
    const credential = await navigator.credentials.create({
      publicKey: publicKeyCredentialCreationOptions
    });
    
    // 4. Prepare credential for server
    const credentialForServer = {
      id: credential.id,
      rawId: arrayBufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        clientDataJSON: arrayBufferToBase64url(credential.response.clientDataJSON),
        attestationObject: arrayBufferToBase64url(credential.response.attestationObject),
        transports: credential.response.getTransports ? credential.response.getTransports() : []
      }
    };
    
    // 5. Send credential to server for verification
    const verifyResponse = await fetch(`${baseURL}/authn/passkeys/register/verify/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ credential: credentialForServer })
    });
    
    const result = await verifyResponse.json();
    return result;
    
  } catch (error) {
    console.error('Passkey registration error:', error);
    throw error;
  }
}

// Authenticate with passkey
export async function authenticateWithPasskey(username = '') {
  try {
    // 1. Get authentication options from server
    const optionsResponse = await fetch(`${baseURL}/authn/passkeys/authenticate/options/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username })
    });
    
    if (!optionsResponse.ok) {
      throw new Error('Failed to get authentication options');
    }
    
    const { options } = await optionsResponse.json();
    
    // 2. Convert options for WebAuthn API
    const publicKeyCredentialRequestOptions = {
      ...options,
      challenge: base64ToArrayBuffer(options.challenge),
      allowCredentials: options.allowCredentials?.map(cred => ({
        ...cred,
        id: base64ToArrayBuffer(cred.id)
      })) || undefined
    };
    
    // Remove empty allowCredentials to trigger platform authenticator UI
    if (publicKeyCredentialRequestOptions.allowCredentials?.length === 0) {
      delete publicKeyCredentialRequestOptions.allowCredentials;
    }
    
    // 3. Get credential
    const credential = await navigator.credentials.get({
      publicKey: publicKeyCredentialRequestOptions
    });
    
    // 4. Prepare credential for server
    const credentialForServer = {
      id: credential.id,
      rawId: arrayBufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        clientDataJSON: arrayBufferToBase64url(credential.response.clientDataJSON),
        authenticatorData: arrayBufferToBase64url(credential.response.authenticatorData),
        signature: arrayBufferToBase64url(credential.response.signature),
        userHandle: credential.response.userHandle ? arrayBufferToBase64url(credential.response.userHandle) : null
      }
    };
    
    // 5. Send credential to server for verification
    const verifyResponse = await fetch(`${baseURL}/authn/passkeys/authenticate/verify/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ credential: credentialForServer })
    });
    
    const result = await verifyResponse.json();
    return result;
    
  } catch (error) {
    console.error('Passkey authentication error:', error);
    throw error;
  }
}

// Get list of user's passkeys
export async function getPasskeys() {
  const response = await fetch(`${baseURL}/authn/passkeys/`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error('Failed to get passkeys');
  }
  
  return response.json();
}

// Delete a passkey
export async function deletePasskey(passkeyId) {
  const response = await fetch(`${baseURL}/authn/passkeys/${passkeyId}/`, {
    method: 'DELETE',
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete passkey');
  }
  
  return response.json();
}

// Check if WebAuthn is supported
export function isWebAuthnSupported() {
  return window.PublicKeyCredential !== undefined &&
         navigator.credentials !== undefined;
} 