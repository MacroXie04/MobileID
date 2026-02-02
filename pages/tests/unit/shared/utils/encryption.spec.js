import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  encryptPassword,
  isEncryptionValid,
  clearPublicKeyCache,
} from '@shared/utils/encryption.js';

// Mock crypto.subtle
const mockImportKey = vi.fn();
const mockEncrypt = vi.fn();

const mockSubtle = {
  importKey: mockImportKey,
  encrypt: mockEncrypt,
};

// Sample RSA public key in PEM format (for testing)
const SAMPLE_PEM_KEY = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
4lgOEePzNm0tRgeLezV6ffAt0gunVTLw7onLRnrq0/IzW7yWR7QkrmBL7jTKEn5u
+qKhbwKfBstIs+bMY2Zkp18gnTxKLxoS2tFczGkPLPgizskuemMghRniWaoLcyeh
kd3qqGElvW/VDL5AaWTg0nLVkjRo9z+40RQzuVaE8AkAFmxZzow3x+VJYKdjykkJ
0iT9wCS0DRTXu269V264Vf/3jvredAQRgOhfqNy2wPn+lVDIZugsH5TQXDq0uxNe
m5rYZZN8NJh0HdN4RB/ETXQJ8pwKdLqN8UPPvz3pPJCpM1B1cH1t4uGZKo1u9LuI
pwIDAQAB
-----END PUBLIC KEY-----`;

describe('encryption utils', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearPublicKeyCache();

    // Setup crypto mock
    Object.defineProperty(window, 'crypto', {
      value: { subtle: mockSubtle },
      writable: true,
      configurable: true,
    });

    // Default mock implementations
    mockImportKey.mockResolvedValue('mock-crypto-key');
    mockEncrypt.mockResolvedValue(new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8]).buffer);
  });

  describe('encryptPassword', () => {
    it('should encrypt password with valid challenge', async () => {
      const challenge = {
        nonce: 'test-nonce-123',
        kid: 'key-id-1',
        public_key: SAMPLE_PEM_KEY,
      };

      const result = await encryptPassword('myPassword123', challenge);

      expect(mockImportKey).toHaveBeenCalledWith(
        'spki',
        expect.any(ArrayBuffer),
        { name: 'RSA-OAEP', hash: 'SHA-256' },
        false,
        ['encrypt']
      );
      expect(mockEncrypt).toHaveBeenCalledTimes(1);
      // Verify the encrypt call received expected structure
      const encryptCall = mockEncrypt.mock.calls[0];
      expect(encryptCall[0]).toEqual({ name: 'RSA-OAEP' });
      expect(encryptCall[1]).toBe('mock-crypto-key');
      // Verify the third argument is typed array-like (Uint8Array)
      expect(encryptCall[2].length).toBeGreaterThan(0);
      expect(encryptCall[2].buffer).toBeDefined();
      expect(typeof result).toBe('string');
      expect(result.length).toBeGreaterThan(0);
    });

    it('should throw error for empty password', async () => {
      const challenge = {
        nonce: 'test-nonce',
        kid: 'key-id',
        public_key: SAMPLE_PEM_KEY,
      };

      await expect(encryptPassword('', challenge)).rejects.toThrow(
        'Password must be a non-empty string'
      );
    });

    it('should throw error for null password', async () => {
      const challenge = {
        nonce: 'test-nonce',
        kid: 'key-id',
        public_key: SAMPLE_PEM_KEY,
      };

      await expect(encryptPassword(null, challenge)).rejects.toThrow(
        'Password must be a non-empty string'
      );
    });

    it('should throw error for non-string password', async () => {
      const challenge = {
        nonce: 'test-nonce',
        kid: 'key-id',
        public_key: SAMPLE_PEM_KEY,
      };

      await expect(encryptPassword(123, challenge)).rejects.toThrow(
        'Password must be a non-empty string'
      );
    });

    it('should throw error for missing challenge', async () => {
      await expect(encryptPassword('password', null)).rejects.toThrow(
        'Login challenge is missing required fields'
      );
    });

    it('should throw error for missing nonce in challenge', async () => {
      const challenge = {
        kid: 'key-id',
        public_key: SAMPLE_PEM_KEY,
      };

      await expect(encryptPassword('password', challenge)).rejects.toThrow(
        'Login challenge is missing required fields'
      );
    });

    it('should throw error for missing kid in challenge', async () => {
      const challenge = {
        nonce: 'test-nonce',
        public_key: SAMPLE_PEM_KEY,
      };

      await expect(encryptPassword('password', challenge)).rejects.toThrow(
        'Login challenge is missing required fields'
      );
    });

    it('should throw error for missing public_key in challenge', async () => {
      const challenge = {
        nonce: 'test-nonce',
        kid: 'key-id',
      };

      await expect(encryptPassword('password', challenge)).rejects.toThrow(
        'Login challenge is missing required fields'
      );
    });

    it('should cache crypto keys by kid', async () => {
      const challenge = {
        nonce: 'test-nonce',
        kid: 'key-id-cache-test',
        public_key: SAMPLE_PEM_KEY,
      };

      // First call
      await encryptPassword('password1', challenge);
      expect(mockImportKey).toHaveBeenCalledTimes(1);

      // Second call with same kid should use cached key
      await encryptPassword('password2', challenge);
      expect(mockImportKey).toHaveBeenCalledTimes(1);
    });

    it('should import different keys for different kids', async () => {
      const challenge1 = {
        nonce: 'test-nonce',
        kid: 'key-id-1',
        public_key: SAMPLE_PEM_KEY,
      };
      const challenge2 = {
        nonce: 'test-nonce',
        kid: 'key-id-2',
        public_key: SAMPLE_PEM_KEY,
      };

      await encryptPassword('password', challenge1);
      await encryptPassword('password', challenge2);

      expect(mockImportKey).toHaveBeenCalledTimes(2);
    });

    it('should clear cache on encryption error and re-throw', async () => {
      mockEncrypt.mockRejectedValueOnce(new Error('Encryption failed'));

      const challenge = {
        nonce: 'test-nonce',
        kid: 'key-id-error',
        public_key: SAMPLE_PEM_KEY,
      };

      await expect(encryptPassword('password', challenge)).rejects.toThrow(
        'Password encryption failed, please try again'
      );

      // The key should be re-imported on next call (cache was cleared)
      mockEncrypt.mockResolvedValueOnce(new Uint8Array([1, 2, 3]).buffer);
      await encryptPassword('password', challenge);

      expect(mockImportKey).toHaveBeenCalledTimes(2);
    });

    it('should throw when crypto.subtle is unavailable', async () => {
      Object.defineProperty(window, 'crypto', {
        value: { subtle: undefined },
        writable: true,
        configurable: true,
      });

      const challenge = {
        nonce: 'test-nonce',
        kid: 'key-id',
        public_key: SAMPLE_PEM_KEY,
      };

      await expect(encryptPassword('password', challenge)).rejects.toThrow(
        'Password encryption failed, please try again'
      );
    });

    it('should include nonce and password in encrypted payload', async () => {
      const challenge = {
        nonce: 'unique-nonce-value',
        kid: 'key-id',
        public_key: SAMPLE_PEM_KEY,
      };

      await encryptPassword('testPassword', challenge);

      // Verify the payload passed to encrypt contains nonce and password
      const encryptCall = mockEncrypt.mock.calls[0];
      const encodedPayload = encryptCall[2];
      const payloadString = new TextDecoder().decode(encodedPayload);
      const payload = JSON.parse(payloadString);

      expect(payload.nonce).toBe('unique-nonce-value');
      expect(payload.password).toBe('testPassword');
    });
  });

  describe('isEncryptionValid', () => {
    it('should return true for string longer than 100 characters', () => {
      const longString = 'a'.repeat(101);
      expect(isEncryptionValid(longString)).toBe(true);
    });

    it('should return false for string with exactly 100 characters', () => {
      const string100 = 'a'.repeat(100);
      expect(isEncryptionValid(string100)).toBe(false);
    });

    it('should return false for short string', () => {
      expect(isEncryptionValid('short')).toBe(false);
    });

    it('should return false for empty string', () => {
      expect(isEncryptionValid('')).toBeFalsy();
    });

    it('should return false for null', () => {
      expect(isEncryptionValid(null)).toBeFalsy();
    });

    it('should return false for undefined', () => {
      expect(isEncryptionValid(undefined)).toBeFalsy();
    });

    it('should return false for number', () => {
      expect(isEncryptionValid(12345678901234567890)).toBe(false);
    });

    it('should return false for object', () => {
      expect(isEncryptionValid({ length: 200 })).toBe(false);
    });
  });

  describe('clearPublicKeyCache', () => {
    it('should clear all cached keys', async () => {
      const challenge = {
        nonce: 'test-nonce',
        kid: 'key-id-clear-test',
        public_key: SAMPLE_PEM_KEY,
      };

      // First call - imports key
      await encryptPassword('password', challenge);
      expect(mockImportKey).toHaveBeenCalledTimes(1);

      // Clear cache
      clearPublicKeyCache();

      // Next call should import key again
      await encryptPassword('password', challenge);
      expect(mockImportKey).toHaveBeenCalledTimes(2);
    });
  });
});
