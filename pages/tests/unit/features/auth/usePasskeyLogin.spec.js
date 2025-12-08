import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { usePasskeyLogin } from '@auth/composables/usePasskeyLogin.js';

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

// Mock API functions
vi.mock('@shared/api/auth.js', () => ({
  passkeyAuthOptions: vi.fn(),
  passkeyAuthVerify: vi.fn(),
  userInfo: vi.fn(),
}));

import { passkeyAuthOptions, passkeyAuthVerify, userInfo } from '@shared/api/auth.js';

describe('usePasskeyLogin', () => {
  let originalCredentials;
  let originalPublicKeyCredential;

  beforeEach(() => {
    // Save original navigator.credentials
    originalCredentials = navigator.credentials;
    originalPublicKeyCredential = window.PublicKeyCredential;

    // Reset all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Restore original navigator.credentials
    Object.defineProperty(navigator, 'credentials', {
      value: originalCredentials,
      writable: true,
      configurable: true,
    });
    window.PublicKeyCredential = originalPublicKeyCredential;
  });

  describe('passkeySupported', () => {
    it('returns true when WebAuthn is supported', () => {
      // Mock WebAuthn support
      window.PublicKeyCredential = vi.fn();
      Object.defineProperty(navigator, 'credentials', {
        value: { get: vi.fn() },
        writable: true,
        configurable: true,
      });

      const { passkeySupported } = usePasskeyLogin();
      expect(passkeySupported.value).toBe(true);
    });

    it('returns false when PublicKeyCredential is not available', () => {
      delete window.PublicKeyCredential;

      const { passkeySupported } = usePasskeyLogin();
      expect(passkeySupported.value).toBe(false);
    });

    it('returns false when navigator.credentials is not available', () => {
      window.PublicKeyCredential = vi.fn();
      Object.defineProperty(navigator, 'credentials', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      const { passkeySupported } = usePasskeyLogin();
      expect(passkeySupported.value).toBe(false);
    });
  });

  describe('handlePasskeyLogin', () => {
    beforeEach(() => {
      // Setup WebAuthn support for login tests
      window.PublicKeyCredential = vi.fn();
    });

    it('sets error when passkey is not supported', async () => {
      delete window.PublicKeyCredential;

      const { handlePasskeyLogin, passkeyError } = usePasskeyLogin();
      await handlePasskeyLogin();

      expect(passkeyError.value).toBe('Passkeys are not supported in this browser.');
    });

    it('calls passkeyAuthOptions to get authentication options', async () => {
      Object.defineProperty(navigator, 'credentials', {
        value: { get: vi.fn().mockRejectedValue(new Error('User cancelled')) },
        writable: true,
        configurable: true,
      });

      passkeyAuthOptions.mockResolvedValue({
        success: true,
        publicKey: {
          challenge: 'dGVzdC1jaGFsbGVuZ2U', // base64url encoded "test-challenge"
          rpId: 'example.com',
          timeout: 60000,
          userVerification: 'required',
        },
      });

      const { handlePasskeyLogin } = usePasskeyLogin();
      await handlePasskeyLogin();

      expect(passkeyAuthOptions).toHaveBeenCalled();
    });

    it('sets loading state during authentication', async () => {
      Object.defineProperty(navigator, 'credentials', {
        value: { get: vi.fn().mockImplementation(() => new Promise(() => {})) },
        writable: true,
        configurable: true,
      });

      passkeyAuthOptions.mockResolvedValue({
        success: true,
        publicKey: {
          challenge: 'dGVzdC1jaGFsbGVuZ2U',
          rpId: 'example.com',
        },
      });

      const { handlePasskeyLogin, passkeyLoading } = usePasskeyLogin();

      expect(passkeyLoading.value).toBe(false);

      const loginPromise = handlePasskeyLogin();

      // Loading should be true during authentication
      expect(passkeyLoading.value).toBe(true);

      // Don't await - just check that loading is set
    });

    it('handles NotAllowedError correctly', async () => {
      Object.defineProperty(navigator, 'credentials', {
        value: {
          get: vi
            .fn()
            .mockRejectedValue(
              Object.assign(new Error('User cancelled'), { name: 'NotAllowedError' })
            ),
        },
        writable: true,
        configurable: true,
      });

      passkeyAuthOptions.mockResolvedValue({
        success: true,
        publicKey: {
          challenge: 'dGVzdC1jaGFsbGVuZ2U',
          rpId: 'example.com',
        },
      });

      const { handlePasskeyLogin, passkeyError } = usePasskeyLogin();
      await handlePasskeyLogin();

      expect(passkeyError.value).toBe('Authentication was cancelled or not allowed.');
    });

    it('handles failed options request', async () => {
      Object.defineProperty(navigator, 'credentials', {
        value: { get: vi.fn() },
        writable: true,
        configurable: true,
      });

      passkeyAuthOptions.mockResolvedValue({
        success: false,
      });

      const { handlePasskeyLogin, passkeyError } = usePasskeyLogin();
      await handlePasskeyLogin();

      expect(passkeyError.value).toBe('Failed to get authentication options');
    });
  });

  describe('clearPasskeyError', () => {
    it('clears the passkey error message', () => {
      delete window.PublicKeyCredential;

      const { handlePasskeyLogin, passkeyError, clearPasskeyError } = usePasskeyLogin();

      // First trigger an error
      handlePasskeyLogin();
      expect(passkeyError.value).not.toBe('');

      // Then clear it
      clearPasskeyError();
      expect(passkeyError.value).toBe('');
    });
  });
});
