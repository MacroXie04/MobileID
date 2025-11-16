import JSEncrypt from 'jsencrypt';
import {apiRequest} from '@/api/client';

// Cache for public key
let cachedPublicKey = null;
let cachedKeyId = null;
let publicKeyPromise = null;

/**
 * Generate a random nonce (hex string)
 * @param {number} bytes - Number of bytes (default: 16)
 * @returns {string} - Hex-encoded nonce
 */
function generateNonce(bytes = 16) {
    const array = new Uint8Array(bytes);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

/**
 * Fetch RSA public key from the backend API
 * @returns {Promise<{kid: string, public_key: string, algorithm: string, key_size: number}>}
 */
async function fetchPublicKey() {
    // If we already have a promise in flight, return it
    if (publicKeyPromise) {
        return publicKeyPromise;
    }

    // Create new promise
    publicKeyPromise = (async () => {
        try {
            const response = await apiRequest('/authn/public-key/');
            cachedPublicKey = response.public_key;
            cachedKeyId = response.kid;
            return response;
        } catch (error) {
            console.error('Failed to fetch public key:', error);
            // Clear promise so we can retry
            publicKeyPromise = null;
            throw new Error('Failed to fetch encryption key. Please try again.');
        } finally {
            // Clear promise after completion (success or failure)
            // This allows retries on subsequent calls
            setTimeout(() => {
                publicKeyPromise = null;
            }, 100);
        }
    })();

    return publicKeyPromise;
}

/**
 * Get the cached public key or fetch it if not available
 * @returns {Promise<string>} - Public key in PEM format
 */
async function getPublicKey() {
    if (cachedPublicKey) {
        return cachedPublicKey;
    }

    const keyData = await fetchPublicKey();
    return keyData.public_key;
}

/**
 * Clear the cached public key (useful for key rotation scenarios)
 */
export function clearPublicKeyCache() {
    cachedPublicKey = null;
    cachedKeyId = null;
    publicKeyPromise = null;
}

/**
 * Fetch the RSA public key from the backend
 * This is exposed for explicit key fetching if needed
 * @returns {Promise<{kid: string, public_key: string, algorithm: string, key_size: number}>}
 */
export async function fetchPublicKeyFromAPI() {
    return fetchPublicKey();
}

/**
 * Encrypt password using RSA public key with nonce
 * 
 * The encryption process:
 * 1. Generate a random nonce (16 bytes = 32 hex chars)
 * 2. Create JSON payload: {"nonce": "...", "password": "..."}
 * 3. Encrypt the entire JSON string using RSA
 * 4. Return Base64-encoded ciphertext
 * 
 * @param {string} password - Plaintext password
 * @returns {Promise<string>} - Encrypted password (Base64 encoded)
 */
export async function encryptPassword(password) {
    try {
        if (!password || typeof password !== 'string') {
            throw new Error('Password must be a non-empty string');
        }

        // Get public key (from cache or fetch)
        const publicKey = await getPublicKey();

        // Generate random nonce (16 bytes = 32 hex characters)
        const nonce = generateNonce(16);

        // Create JSON payload
        const payload = JSON.stringify({
            nonce: nonce,
            password: password
        });

        // Encrypt using JSEncrypt
        const encrypt = new JSEncrypt();
        encrypt.setPublicKey(publicKey);
        const encrypted = encrypt.encrypt(payload);
        
        if (!encrypted) {
            throw new Error('RSA encryption failed - public key may be invalid');
        }
        
        return encrypted;
    } catch (error) {
        console.error('Password encryption error:', error);
        
        // If it's a key fetch error, clear cache and rethrow
        if (error.message.includes('Failed to fetch encryption key')) {
            clearPublicKeyCache();
        }
        
        throw new Error('Password encryption failed, please try again');
    }
}

/**
 * Validate if encryption was successful
 * @param {string} encryptedPassword - Encrypted password
 * @returns {boolean} - Whether encryption was successful
 */
export function isEncryptionValid(encryptedPassword) {
    return encryptedPassword && typeof encryptedPassword === 'string' && encryptedPassword.length > 100;
}
