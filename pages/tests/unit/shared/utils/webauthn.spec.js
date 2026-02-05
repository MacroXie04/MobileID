import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  isWebAuthnSupported,
  base64urlToBuffer,
  bufferToBase64url,
  preparePublicKeyOptions,
  serializeCredential,
} from '@shared/utils/webauthn.js';

describe('webauthn utils', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('isWebAuthnSupported', () => {
    it('should return true when PublicKeyCredential and navigator.credentials exist', () => {
      window.PublicKeyCredential = vi.fn();
      Object.defineProperty(navigator, 'credentials', {
        value: { get: vi.fn() },
        writable: true,
        configurable: true,
      });

      expect(isWebAuthnSupported()).toBe(true);
    });

    it('should return false when PublicKeyCredential is missing', () => {
      delete window.PublicKeyCredential;
      Object.defineProperty(navigator, 'credentials', {
        value: { get: vi.fn() },
        writable: true,
        configurable: true,
      });

      expect(isWebAuthnSupported()).toBe(false);
    });

    it('should return false when PublicKeyCredential is not a function', () => {
      window.PublicKeyCredential = 'not a function';
      Object.defineProperty(navigator, 'credentials', {
        value: { get: vi.fn() },
        writable: true,
        configurable: true,
      });

      expect(isWebAuthnSupported()).toBe(false);
    });

    it('should return false when navigator.credentials is missing', () => {
      window.PublicKeyCredential = vi.fn();
      Object.defineProperty(navigator, 'credentials', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      expect(isWebAuthnSupported()).toBe(false);
    });

    it('should return false when navigator.credentials.get is not a function', () => {
      window.PublicKeyCredential = vi.fn();
      Object.defineProperty(navigator, 'credentials', {
        value: { get: 'not a function' },
        writable: true,
        configurable: true,
      });

      expect(isWebAuthnSupported()).toBe(false);
    });
  });

  describe('base64urlToBuffer', () => {
    it('should decode valid base64url strings', () => {
      // "Hello" in base64url is "SGVsbG8"
      const buffer = base64urlToBuffer('SGVsbG8');
      const bytes = new Uint8Array(buffer);
      const decoded = String.fromCharCode(...bytes);

      expect(decoded).toBe('Hello');
    });

    it('should handle URL-safe characters (- and _)', () => {
      // Base64url uses - instead of + and _ instead of /
      // "???" in standard base64 might be "+/+" but in base64url is "-_-"
      // Let's use a known value: binary [251, 239, 190] = "/+++" in base64 = "_--_" in base64url
      const buffer = base64urlToBuffer('--__');
      const bytes = new Uint8Array(buffer);

      // This should decode without error
      expect(bytes.length).toBeGreaterThan(0);
    });

    it('should handle padding correctly - no padding needed', () => {
      // "abc" (3 bytes) = "YWJj" (no padding)
      const buffer = base64urlToBuffer('YWJj');
      const bytes = new Uint8Array(buffer);
      const decoded = String.fromCharCode(...bytes);

      expect(decoded).toBe('abc');
    });

    it('should handle padding correctly - 1 padding char needed', () => {
      // "ab" (2 bytes) = "YWI" in base64url (needs 1 padding char)
      const buffer = base64urlToBuffer('YWI');
      const bytes = new Uint8Array(buffer);
      const decoded = String.fromCharCode(...bytes);

      expect(decoded).toBe('ab');
    });

    it('should handle padding correctly - 2 padding chars needed', () => {
      // "a" (1 byte) = "YQ" in base64url (needs 2 padding chars)
      const buffer = base64urlToBuffer('YQ');
      const bytes = new Uint8Array(buffer);
      const decoded = String.fromCharCode(...bytes);

      expect(decoded).toBe('a');
    });

    it('should handle empty string', () => {
      const buffer = base64urlToBuffer('');
      expect(buffer.byteLength).toBe(0);
    });
  });

  describe('bufferToBase64url', () => {
    it('should encode ArrayBuffer to base64url', () => {
      const bytes = new Uint8Array([72, 101, 108, 108, 111]); // "Hello"
      const result = bufferToBase64url(bytes.buffer);

      expect(result).toBe('SGVsbG8');
    });

    it('should remove padding', () => {
      const bytes = new Uint8Array([97]); // "a" - would be "YQ==" in standard base64
      const result = bufferToBase64url(bytes.buffer);

      expect(result).toBe('YQ');
      expect(result).not.toContain('=');
    });

    it('should use URL-safe characters', () => {
      // Create bytes that would produce + and / in standard base64
      const bytes = new Uint8Array([251, 239, 190]); // produces base64 with + and /
      const result = bufferToBase64url(bytes.buffer);

      expect(result).not.toContain('+');
      expect(result).not.toContain('/');
    });

    it('should handle empty buffer', () => {
      const bytes = new Uint8Array([]);
      const result = bufferToBase64url(bytes.buffer);

      expect(result).toBe('');
    });

    it('should roundtrip correctly', () => {
      const original = 'Test string 123!@#';
      const bytes = new Uint8Array(original.split('').map((c) => c.charCodeAt(0)));

      const encoded = bufferToBase64url(bytes.buffer);
      const decoded = base64urlToBuffer(encoded);
      const decodedBytes = new Uint8Array(decoded);
      const decodedString = String.fromCharCode(...decodedBytes);

      expect(decodedString).toBe(original);
    });
  });

  describe('preparePublicKeyOptions', () => {
    it('should convert challenge from base64url string to ArrayBuffer', () => {
      const options = {
        challenge: 'SGVsbG8', // "Hello" in base64url
        timeout: 60000,
      };

      const prepared = preparePublicKeyOptions(options);

      expect(prepared.challenge).toBeInstanceOf(ArrayBuffer);
      const bytes = new Uint8Array(prepared.challenge);
      const decoded = String.fromCharCode(...bytes);
      expect(decoded).toBe('Hello');
    });

    it('should leave challenge unchanged if already ArrayBuffer', () => {
      const challengeBuffer = new Uint8Array([1, 2, 3]).buffer;
      const options = {
        challenge: challengeBuffer,
        timeout: 60000,
      };

      const prepared = preparePublicKeyOptions(options);

      expect(prepared.challenge).toBe(challengeBuffer);
    });

    it('should convert allowCredentials IDs from base64url to ArrayBuffer', () => {
      const options = {
        challenge: 'Y2hhbGxlbmdl',
        allowCredentials: [
          { id: 'Y3JlZDE', type: 'public-key' },
          { id: 'Y3JlZDI', type: 'public-key' },
        ],
      };

      const prepared = preparePublicKeyOptions(options);

      expect(prepared.allowCredentials).toHaveLength(2);
      expect(prepared.allowCredentials[0].id).toBeInstanceOf(ArrayBuffer);
      expect(prepared.allowCredentials[1].id).toBeInstanceOf(ArrayBuffer);

      // Verify content
      const id1Bytes = new Uint8Array(prepared.allowCredentials[0].id);
      const id1Decoded = String.fromCharCode(...id1Bytes);
      expect(id1Decoded).toBe('cred1');
    });

    it('should leave allowCredentials IDs unchanged if already ArrayBuffer', () => {
      const idBuffer = new Uint8Array([1, 2, 3]).buffer;
      const options = {
        challenge: 'Y2hhbGxlbmdl',
        allowCredentials: [{ id: idBuffer, type: 'public-key' }],
      };

      const prepared = preparePublicKeyOptions(options);

      expect(prepared.allowCredentials[0].id).toBe(idBuffer);
    });

    it('should preserve other allowCredentials properties', () => {
      const options = {
        challenge: 'Y2hhbGxlbmdl',
        allowCredentials: [{ id: 'Y3JlZDE', type: 'public-key', transports: ['usb', 'nfc'] }],
      };

      const prepared = preparePublicKeyOptions(options);

      expect(prepared.allowCredentials[0].type).toBe('public-key');
      expect(prepared.allowCredentials[0].transports).toEqual(['usb', 'nfc']);
    });

    it('should handle options without allowCredentials', () => {
      const options = {
        challenge: 'Y2hhbGxlbmdl',
        timeout: 60000,
        rpId: 'example.com',
      };

      const prepared = preparePublicKeyOptions(options);

      expect(prepared.allowCredentials).toBeUndefined();
      expect(prepared.timeout).toBe(60000);
      expect(prepared.rpId).toBe('example.com');
    });

    it('should not modify the original options object', () => {
      const original = {
        challenge: 'Y2hhbGxlbmdl',
        timeout: 60000,
      };
      const originalChallenge = original.challenge;

      preparePublicKeyOptions(original);

      expect(original.challenge).toBe(originalChallenge);
    });
  });

  describe('serializeCredential', () => {
    it('should serialize all credential fields', () => {
      const credential = {
        id: 'credential-id',
        rawId: new Uint8Array([1, 2, 3]).buffer,
        type: 'public-key',
        response: {
          clientDataJSON: new Uint8Array([4, 5, 6]).buffer,
          authenticatorData: new Uint8Array([7, 8, 9]).buffer,
          signature: new Uint8Array([10, 11, 12]).buffer,
          userHandle: new Uint8Array([13, 14, 15]).buffer,
        },
      };

      const serialized = serializeCredential(credential);

      expect(serialized.id).toBe('credential-id');
      expect(typeof serialized.rawId).toBe('string');
      expect(serialized.type).toBe('public-key');
      expect(typeof serialized.response.clientDataJSON).toBe('string');
      expect(typeof serialized.response.authenticatorData).toBe('string');
      expect(typeof serialized.response.signature).toBe('string');
      expect(typeof serialized.response.userHandle).toBe('string');
    });

    it('should convert all ArrayBuffers to base64url', () => {
      const credential = {
        id: 'test-id',
        rawId: new Uint8Array([72, 101, 108, 108, 111]).buffer, // "Hello"
        type: 'public-key',
        response: {
          clientDataJSON: new Uint8Array([87, 111, 114, 108, 100]).buffer, // "World"
          authenticatorData: new Uint8Array([1, 2, 3]).buffer,
          signature: new Uint8Array([4, 5, 6]).buffer,
          userHandle: new Uint8Array([7, 8, 9]).buffer,
        },
      };

      const serialized = serializeCredential(credential);

      expect(serialized.rawId).toBe('SGVsbG8');
      expect(serialized.response.clientDataJSON).toBe('V29ybGQ');
    });

    it('should handle null userHandle', () => {
      const credential = {
        id: 'test-id',
        rawId: new Uint8Array([1, 2, 3]).buffer,
        type: 'public-key',
        response: {
          clientDataJSON: new Uint8Array([4, 5, 6]).buffer,
          authenticatorData: new Uint8Array([7, 8, 9]).buffer,
          signature: new Uint8Array([10, 11, 12]).buffer,
          userHandle: null,
        },
      };

      const serialized = serializeCredential(credential);

      expect(serialized.response.userHandle).toBeNull();
    });

    it('should handle undefined userHandle', () => {
      const credential = {
        id: 'test-id',
        rawId: new Uint8Array([1, 2, 3]).buffer,
        type: 'public-key',
        response: {
          clientDataJSON: new Uint8Array([4, 5, 6]).buffer,
          authenticatorData: new Uint8Array([7, 8, 9]).buffer,
          signature: new Uint8Array([10, 11, 12]).buffer,
          userHandle: undefined,
        },
      };

      const serialized = serializeCredential(credential);

      expect(serialized.response.userHandle).toBeNull();
    });

    it('should preserve credential id as-is (not encoded)', () => {
      const credential = {
        id: 'original-credential-id-123',
        rawId: new Uint8Array([1]).buffer,
        type: 'public-key',
        response: {
          clientDataJSON: new Uint8Array([1]).buffer,
          authenticatorData: new Uint8Array([1]).buffer,
          signature: new Uint8Array([1]).buffer,
          userHandle: null,
        },
      };

      const serialized = serializeCredential(credential);

      expect(serialized.id).toBe('original-credential-id-123');
    });
  });
});
