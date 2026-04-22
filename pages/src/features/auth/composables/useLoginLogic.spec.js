import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { nextTick } from 'vue';

const mockLogin = vi.fn();
const mockEstablishSession = vi.fn();
vi.mock('@shared/api/auth.js', () => ({
  login: (...args) => mockLogin(...args),
  establishAuthenticatedSession: (...args) => mockEstablishSession(...args),
}));

const mockSetUserInfo = vi.fn();
vi.mock('@shared/state/authState', () => ({
  setUserInfo: (info) => mockSetUserInfo(info),
}));

const mockRouterPush = vi.fn();
let mockRoute = { query: {} };
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: (path) => mockRouterPush(path) }),
  useRoute: () => mockRoute,
}));

// Import after mocks are registered.
import { useLoginLogic } from '@auth/composables/useLoginLogic.js';
import { ApiError } from '@shared/api/client.js';

function fillCreds(login) {
  login.formData.username = 'alice';
  login.formData.password = 'pw';
}

describe('useLoginLogic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute = { query: {} };
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('exposes empty initial formData and non-loading state', () => {
    const login = useLoginLogic();

    expect(login.formData.username).toBe('');
    expect(login.formData.password).toBe('');
    expect(login.loading.value).toBe(false);
    expect(login.registrationSuccess.value).toBe(false);
  });

  it('flips registrationSuccess when the `registered=true` query is present', () => {
    mockRoute = { query: { registered: 'true' } };

    const login = useLoginLogic();

    expect(login.registrationSuccess.value).toBe(true);
  });

  it('does not call the API when the form is invalid', async () => {
    const login = useLoginLogic();

    await login.handleSubmit();

    expect(mockLogin).not.toHaveBeenCalled();
    expect(login.errors.username).toBe('Username is required');
    expect(login.errors.password).toBe('Password is required');
    expect(login.loading.value).toBe(false);
  });

  it('happy path: logs in, establishes session, sets user info, navigates home', async () => {
    mockLogin.mockResolvedValue({ message: 'Login successful' });
    mockEstablishSession.mockResolvedValue({ username: 'alice' });
    const login = useLoginLogic();
    fillCreds(login);

    await login.handleSubmit();

    expect(mockLogin).toHaveBeenCalledWith('alice', 'pw');
    expect(mockEstablishSession).toHaveBeenCalledTimes(1);
    expect(mockSetUserInfo).toHaveBeenCalledWith({ username: 'alice' });
    expect(mockRouterPush).toHaveBeenCalledWith('/');
    expect(login.loading.value).toBe(false);
  });

  it('surfaces a session-establishment error when session cannot be restored', async () => {
    mockLogin.mockResolvedValue({ message: 'Login successful' });
    mockEstablishSession.mockResolvedValue(null);
    const login = useLoginLogic();
    fillCreds(login);

    await login.handleSubmit();

    expect(mockRouterPush).not.toHaveBeenCalled();
    expect(mockSetUserInfo).not.toHaveBeenCalled();
    expect(login.errors.general).toMatch(/session could not be established/i);
  });

  it('surfaces a generic error when login response lacks the success message', async () => {
    mockLogin.mockResolvedValue({ message: 'something else' });
    const login = useLoginLogic();
    fillCreds(login);

    await login.handleSubmit();

    expect(login.errors.general).toBe('Unable to sign in. Please try again.');
    expect(mockEstablishSession).not.toHaveBeenCalled();
  });

  it('surfaces the server-provided detail on ApiError (e.g. 401)', async () => {
    mockLogin.mockRejectedValue(
      new ApiError('Unauthorized', 401, { detail: 'Invalid credentials' })
    );
    const login = useLoginLogic();
    fillCreds(login);

    await login.handleSubmit();

    expect(login.errors.general).toBe('Invalid credentials');
    expect(mockRouterPush).not.toHaveBeenCalled();
  });

  it('falls back to a generic ApiError message when no detail is provided', async () => {
    mockLogin.mockRejectedValue(new ApiError('Locked', 423, {}));
    const login = useLoginLogic();
    fillCreds(login);

    await login.handleSubmit();

    expect(login.errors.general).toBe('Invalid username or password.');
  });

  it('reports a network error for non-ApiError failures', async () => {
    mockLogin.mockRejectedValue(new TypeError('fetch failed'));
    const login = useLoginLogic();
    fillCreds(login);

    await login.handleSubmit();

    expect(login.errors.general).toMatch(/network error/i);
  });

  it('toggles loading state around the async call and resets on failure', async () => {
    let releaseLogin;
    mockLogin.mockImplementation(
      () =>
        new Promise((resolve) => {
          releaseLogin = resolve;
        })
    );
    const login = useLoginLogic();
    fillCreds(login);

    const submitPromise = login.handleSubmit();
    await nextTick();
    expect(login.loading.value).toBe(true);

    releaseLogin({ message: 'something else' });
    await submitPromise;

    expect(login.loading.value).toBe(false);
  });

  it('validateField helper delegates to the shared validator with current formData', () => {
    const login = useLoginLogic();
    login.formData.username = '';

    login.validateField('username');

    expect(login.errors.username).toBe('Username is required');
  });

  it('clearError removes a previously-set field error', () => {
    const login = useLoginLogic();
    login.validateField('username');
    expect(login.errors.username).toBeDefined();

    login.clearError('username');

    expect(login.errors.username).toBeUndefined();
  });
});
