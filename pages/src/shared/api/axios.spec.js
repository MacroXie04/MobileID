import { beforeEach, describe, expect, it, vi } from 'vitest';

// Capture the axios create() arguments and the response interceptor pair that
// axios.js registers, so we can invoke the error handler directly.
const capturedCreate = { config: null, interceptor: null };
const apiCallMock = vi.fn();

vi.mock('axios', () => {
  const create = vi.fn((config) => {
    capturedCreate.config = config;
    const instance = (...args) => apiCallMock(...args);
    instance.interceptors = {
      response: {
        use: (onFulfilled, onRejected) => {
          capturedCreate.interceptor = { onFulfilled, onRejected };
        },
      },
    };
    return instance;
  });
  return { default: { create }, create };
});

vi.mock('@app/config/config', () => ({
  baseURL: 'https://api.example.test/',
}));

const mockClearAuthCookies = vi.fn();
const mockClearAuthStorage = vi.fn();
vi.mock('@shared/utils/cookie', () => ({
  clearAuthCookies: () => mockClearAuthCookies(),
  clearAuthStorage: () => mockClearAuthStorage(),
}));

const mockRefreshToken = vi.fn();
vi.mock('@shared/utils/tokenRefresh', () => ({
  refreshToken: () => mockRefreshToken(),
}));

const mockRouterPush = vi.fn();
vi.mock('@app/router/index.js', () => ({
  default: { push: (path) => mockRouterPush(path) },
}));

async function loadAxios() {
  capturedCreate.config = null;
  capturedCreate.interceptor = null;
  apiCallMock.mockReset();
  vi.resetModules();
  const mod = await import('@shared/api/axios.js');
  return mod.default;
}

function make401(url = '/authn/user_info/', extra = {}) {
  return {
    response: { status: 401 },
    config: { url, ...extra },
  };
}

describe('axios instance configuration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates the instance with the configured baseURL and CSRF settings', async () => {
    await loadAxios();

    expect(capturedCreate.config).toMatchObject({
      baseURL: 'https://api.example.test/',
      withCredentials: true,
      xsrfCookieName: 'csrftoken',
      xsrfHeaderName: 'X-CSRFToken',
    });
    expect(capturedCreate.config.headers).toMatchObject({
      'Content-Type': 'application/json',
    });
  });

  it('registers a response interceptor pair on the instance', async () => {
    await loadAxios();

    expect(capturedCreate.interceptor).not.toBeNull();
    // Success handler passes responses through unchanged.
    const res = { data: {} };
    expect(capturedCreate.interceptor.onFulfilled(res)).toBe(res);
  });
});

describe('axios response error handler', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { pathname: '/dashboard', href: '/dashboard' },
    });
    await loadAxios();
  });

  it('passes through errors without a 401 response', async () => {
    const err = { response: { status: 500 }, config: { url: '/foo' } };

    await expect(capturedCreate.interceptor.onRejected(err)).rejects.toBe(err);
    expect(mockRefreshToken).not.toHaveBeenCalled();
  });

  it('does not retry the refresh endpoint itself', async () => {
    const err = make401('/authn/token/refresh/');

    await expect(capturedCreate.interceptor.onRejected(err)).rejects.toBe(err);
    expect(mockRefreshToken).not.toHaveBeenCalled();
  });

  it('retries the request once after a successful token refresh', async () => {
    mockRefreshToken.mockResolvedValue(true);
    apiCallMock.mockResolvedValue({ data: 'retry ok' });
    const err = make401();

    const result = await capturedCreate.interceptor.onRejected(err);

    expect(mockRefreshToken).toHaveBeenCalledTimes(1);
    expect(apiCallMock).toHaveBeenCalledWith(
      expect.objectContaining({ _retry: true, url: '/authn/user_info/' }),
    );
    expect(result).toEqual({ data: 'retry ok' });
  });

  it('does not retry a request that has already been retried once', async () => {
    mockRefreshToken.mockResolvedValue(true);
    const err = make401('/authn/user_info/', { _retry: true });

    await expect(capturedCreate.interceptor.onRejected(err)).rejects.toBe(err);
    expect(mockRefreshToken).not.toHaveBeenCalled();
    expect(apiCallMock).not.toHaveBeenCalled();
  });

  it('clears auth state and redirects to /login when refresh fails', async () => {
    mockRefreshToken.mockResolvedValue(false);
    const err = make401();

    await expect(capturedCreate.interceptor.onRejected(err)).rejects.toBe(err);

    expect(mockClearAuthCookies).toHaveBeenCalled();
    expect(mockClearAuthStorage).toHaveBeenCalled();
    expect(mockRouterPush).toHaveBeenCalledWith('/login');
  });

  it('does not redirect when already on the login page', async () => {
    window.location.pathname = '/login';
    mockRefreshToken.mockResolvedValue(false);
    const err = make401();

    await expect(capturedCreate.interceptor.onRejected(err)).rejects.toBe(err);

    expect(mockRouterPush).not.toHaveBeenCalled();
  });

  it('clears auth state when refresh throws', async () => {
    mockRefreshToken.mockRejectedValue(new Error('network'));
    const err = make401();

    await expect(capturedCreate.interceptor.onRejected(err)).rejects.toBe(err);

    expect(mockClearAuthCookies).toHaveBeenCalled();
    expect(mockClearAuthStorage).toHaveBeenCalled();
  });
});
