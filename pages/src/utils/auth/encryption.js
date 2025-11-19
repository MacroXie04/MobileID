const keyCache = new Map();

function ensureCryptoSupport() {
    if (typeof window === 'undefined' || !window.crypto?.subtle) {
        throw new Error('Secure cryptography APIs are unavailable in this environment.');
    }
    return window.crypto.subtle;
}

function pemToArrayBuffer(pem) {
    const b64 = pem.replace(/-----BEGIN PUBLIC KEY-----/g, '')
        .replace(/-----END PUBLIC KEY-----/g, '')
        .replace(/\s+/g, '');
    const binary = atob(b64);
    const buffer = new ArrayBuffer(binary.length);
    const view = new Uint8Array(buffer);
    for (let i = 0; i < binary.length; i += 1) {
        view[i] = binary.charCodeAt(i);
    }
    return buffer;
}

function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i += 1) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

async function getCryptoKeyForKid(kid, publicKey) {
    if (keyCache.has(kid)) {
        return keyCache.get(kid);
    }

    const subtle = ensureCryptoSupport();
    const binaryDer = pemToArrayBuffer(publicKey);
    const cryptoKey = await subtle.importKey(
        'spki',
        binaryDer,
        {
            name: 'RSA-OAEP',
            hash: 'SHA-256',
        },
        false,
        ['encrypt'],
    );

    keyCache.set(kid, cryptoKey);
    return cryptoKey;
}

export function clearPublicKeyCache() {
    keyCache.clear();
}

/**
 * Encrypt password using RSA-OAEP with a server-provided challenge.
 * @param {string} password
 * @param {{nonce: string, kid: string, public_key: string}} challenge
 * @returns {Promise<string>}
 */
export async function encryptPassword(password, challenge) {
    if (!password || typeof password !== 'string') {
        throw new Error('Password must be a non-empty string');
    }
    if (!challenge || !challenge.nonce || !challenge.kid || !challenge.public_key) {
        throw new Error('Login challenge is missing required fields');
    }

    try {
        const cryptoKey = await getCryptoKeyForKid(challenge.kid, challenge.public_key);
        const payload = JSON.stringify({
            nonce: challenge.nonce,
            password,
        });
        const encodedPayload = new TextEncoder().encode(payload);
        const subtle = ensureCryptoSupport();
        const encrypted = await subtle.encrypt(
            {
                name: 'RSA-OAEP',
            },
            cryptoKey,
            encodedPayload,
        );
        return arrayBufferToBase64(encrypted);
    } catch (error) {
        console.error('Password encryption error:', error);
        clearPublicKeyCache();
        throw new Error('Password encryption failed, please try again');
    }
}

export function isEncryptionValid(encryptedPassword) {
    return encryptedPassword && typeof encryptedPassword === 'string' && encryptedPassword.length > 100;
}
