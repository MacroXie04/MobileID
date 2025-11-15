import JSEncrypt from 'jsencrypt';

// RSA public key - used for password encryption
const RSA_PUBLIC_KEY = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs1+w8lZHoAGEJjG63ZVu
JdhV8Z+92t5GY2hlwhtzkAcwZ+sPR4YUmRSqWnA29B6z5tVTrQfEtHhqA8fKwmAv
02REWVe8LXUM7VHjKvkyWqzwiKy4g1kUvewkMRj1GlOtm6FXW/k7irMZdB4sTCS2
7Y25lE9m5Krn55EAPU+goYDmZYTwKxgemz5oEagGcDILQylgRNPEbWmp6HvanLso
gzor+xVoAZ2//ke72myVS8WYCePxjrMy1ezofuUWoPeMyhSIFRvMQmMKWIuVh9h2
/DrpfMpVthRaAUW4Q238F4QlcIz+pKj9R8r8uFjgAozySW90vxFJp1O8AWo0ARsl
LwIDAQAB
-----END PUBLIC KEY-----`;

/**
 * Encrypt password using RSA public key
 * @param {string} password - Plaintext password
 * @returns {string} - Encrypted password (Base64 encoded)
 */
export function encryptPassword(password) {
    try {
        console.log('Starting password encryption:', password);
        const encrypt = new JSEncrypt();
        encrypt.setPublicKey(RSA_PUBLIC_KEY);
        const encrypted = encrypt.encrypt(password);
        
        console.log('Encryption result:', encrypted);
        console.log('Encryption result length:', encrypted ? encrypted.length : 0);
        
        if (!encrypted) {
            throw new Error('Password encryption failed');
        }
        
        return encrypted;
    } catch (error) {
        console.error('Password encryption error:', error);
        throw new Error('Password encryption failed, please try again');
    }
}

/**
 * Validate if encryption was successful
 * @param {string} encryptedPassword - Encrypted password
 * @returns {boolean} - Whether encryption was successful
 */
export function isEncryptionValid(encryptedPassword) {
    return encryptedPassword && encryptedPassword.length > 0;
}
