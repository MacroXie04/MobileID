import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Helpers to stub the browser APIs the composable consumes. The module has a
// side-effectful checkExistingPermission() call on import, so we must install
// the stubs before each fresh import.

function installPermissionsStub({ state = 'prompt' } = {}) {
  const listeners = [];
  const result = {
    state,
    addEventListener: (_event, fn) => listeners.push(fn),
    removeEventListener: (_event, fn) => {
      const idx = listeners.indexOf(fn);
      if (idx >= 0) listeners.splice(idx, 1);
    },
    fire: () => listeners.forEach((fn) => fn()),
  };
  const query = vi.fn().mockResolvedValue(result);
  globalThis.navigator = {
    ...globalThis.navigator,
    permissions: { query },
    mediaDevices: globalThis.navigator?.mediaDevices,
  };
  return { result, query };
}

function installMediaDevicesStub(getUserMedia) {
  globalThis.navigator = {
    ...globalThis.navigator,
    mediaDevices: { getUserMedia },
  };
}

function fakeStream() {
  const track = { stop: vi.fn() };
  return {
    _tracks: [track],
    getTracks: () => [track],
  };
}

async function loadComposable() {
  vi.resetModules();
  const mod = await import('@shared/composables/device/useCameraPermission');
  // Let the side-effectful checkExistingPermission() microtask settle.
  await Promise.resolve();
  await Promise.resolve();
  return mod.useCameraPermission();
}

describe('useCameraPermission — initial permission check', () => {
  afterEach(() => {
    delete globalThis.navigator.permissions;
    delete globalThis.navigator.mediaDevices;
  });

  it('marks permission granted when Permissions API reports granted', async () => {
    installPermissionsStub({ state: 'granted' });

    const cam = await loadComposable();

    expect(cam.hasCameraPermission.value).toBe(true);
    expect(cam.permissionDenied.value).toBe(false);
  });

  it('marks permission denied when Permissions API reports denied', async () => {
    installPermissionsStub({ state: 'denied' });

    const cam = await loadComposable();

    expect(cam.hasCameraPermission.value).toBe(false);
    expect(cam.permissionDenied.value).toBe(true);
  });

  it('stays neutral when Permissions API reports prompt', async () => {
    installPermissionsStub({ state: 'prompt' });

    const cam = await loadComposable();

    expect(cam.hasCameraPermission.value).toBe(false);
    expect(cam.permissionDenied.value).toBe(false);
  });

  it('does not crash when Permissions API is unavailable', async () => {
    // No navigator.permissions at all
    globalThis.navigator = { ...globalThis.navigator };
    delete globalThis.navigator.permissions;

    const cam = await loadComposable();

    expect(cam.hasCameraPermission.value).toBe(false);
    expect(cam.permissionDenied.value).toBe(false);
  });

  it('reacts to permissionStatus change events', async () => {
    const { result } = installPermissionsStub({ state: 'prompt' });

    const cam = await loadComposable();
    expect(cam.hasCameraPermission.value).toBe(false);

    // Simulate the browser transitioning to granted.
    result.state = 'granted';
    result.fire();

    expect(cam.hasCameraPermission.value).toBe(true);
    expect(cam.permissionDenied.value).toBe(false);
  });

  it('reacts when permission transitions to denied', async () => {
    const { result } = installPermissionsStub({ state: 'prompt' });

    const cam = await loadComposable();

    result.state = 'denied';
    result.fire();

    expect(cam.permissionDenied.value).toBe(true);
    expect(cam.hasCameraPermission.value).toBe(false);
  });

  it('swallows errors thrown by navigator.permissions.query', async () => {
    const query = vi.fn().mockRejectedValue(new Error('no query for you'));
    globalThis.navigator = {
      ...globalThis.navigator,
      permissions: { query },
    };

    const cam = await loadComposable();

    expect(cam.isCheckingPermission.value).toBe(false);
    expect(cam.hasCameraPermission.value).toBe(false);
  });
});

describe('useCameraPermission — ensureCameraPermission', () => {
  beforeEach(() => {
    installPermissionsStub({ state: 'prompt' });
  });

  afterEach(() => {
    delete globalThis.navigator.mediaDevices;
    delete globalThis.navigator.permissions;
  });

  it('returns granted + stream when getUserMedia succeeds', async () => {
    const stream = fakeStream();
    installMediaDevicesStub(vi.fn().mockResolvedValue(stream));

    const cam = await loadComposable();
    const result = await cam.ensureCameraPermission();

    expect(result).toEqual({ granted: true, stream, error: null });
    expect(cam.hasCameraPermission.value).toBe(true);
    expect(cam.permissionDenied.value).toBe(false);
  });

  it('stops tracks and returns null stream when stopStream is true', async () => {
    const stream = fakeStream();
    installMediaDevicesStub(vi.fn().mockResolvedValue(stream));

    const cam = await loadComposable();
    const result = await cam.ensureCameraPermission({ stopStream: true });

    expect(result).toEqual({ granted: true, stream: null, error: null });
    expect(stream._tracks[0].stop).toHaveBeenCalledTimes(1);
  });

  it('passes the requested facingMode through to getUserMedia', async () => {
    const getUserMedia = vi.fn().mockResolvedValue(fakeStream());
    installMediaDevicesStub(getUserMedia);

    const cam = await loadComposable();
    await cam.ensureCameraPermission({ facingMode: 'user' });

    expect(getUserMedia).toHaveBeenCalledWith(
      expect.objectContaining({
        video: expect.objectContaining({ facingMode: 'user' }),
      })
    );
  });

  it('returns a "Camera not supported" error when mediaDevices is missing', async () => {
    // No getUserMedia installed.
    globalThis.navigator = { ...globalThis.navigator, mediaDevices: undefined };

    const cam = await loadComposable();
    const result = await cam.ensureCameraPermission();

    expect(result).toEqual({
      granted: false,
      stream: null,
      error: 'Camera not supported',
    });
  });

  it('marks permission denied when getUserMedia rejects with NotAllowedError', async () => {
    const err = Object.assign(new Error('denied'), { name: 'NotAllowedError' });
    installMediaDevicesStub(vi.fn().mockRejectedValue(err));

    const cam = await loadComposable();
    const result = await cam.ensureCameraPermission();

    expect(result).toEqual({
      granted: false,
      stream: null,
      error: 'denied',
    });
    expect(cam.hasCameraPermission.value).toBe(false);
    expect(cam.permissionDenied.value).toBe(true);
  });

  it('does not flag permissionDenied for non-permission errors', async () => {
    const err = Object.assign(new Error('hardware gone'), {
      name: 'NotFoundError',
    });
    installMediaDevicesStub(vi.fn().mockRejectedValue(err));

    const cam = await loadComposable();
    const result = await cam.ensureCameraPermission();

    expect(result.granted).toBe(false);
    expect(result.error).toBe('hardware gone');
    expect(cam.permissionDenied.value).toBe(false);
  });
});
