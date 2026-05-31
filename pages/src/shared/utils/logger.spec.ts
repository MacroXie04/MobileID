import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// `noisyEnabled` is captured at module-load time from import.meta.env, so each
// scenario stubs the env and re-imports the module via resetModules + dynamic import.
async function loadLogger() {
  vi.resetModules();
  const mod = await import('./logger');
  return mod.logger;
}

describe('logger', () => {
  beforeEach(() => {
    vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.spyOn(console, 'info').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('silences debug/info under test mode (DEV false / MODE test)', async () => {
    vi.stubEnv('DEV', false);
    vi.stubEnv('MODE', 'test');
    const logger = await loadLogger();

    logger.debug('trace', { a: 1 });
    logger.info('info trace');

    expect(console.debug).not.toHaveBeenCalled();
    expect(console.info).not.toHaveBeenCalled();
  });

  it('silences debug/info in dev mode when MODE is test', async () => {
    // DEV true but MODE 'test' (e.g. a dev-flavored test run) must still be silent.
    vi.stubEnv('DEV', true);
    vi.stubEnv('MODE', 'test');
    const logger = await loadLogger();

    logger.debug('trace');
    logger.info('info');

    expect(console.debug).not.toHaveBeenCalled();
    expect(console.info).not.toHaveBeenCalled();
  });

  it('emits debug/info only in real dev mode (DEV true / MODE development)', async () => {
    vi.stubEnv('DEV', true);
    vi.stubEnv('MODE', 'development');
    const logger = await loadLogger();

    logger.debug('trace', 1, 2);
    logger.info('info', { x: true });

    expect(console.debug).toHaveBeenCalledWith('trace', 1, 2);
    expect(console.info).toHaveBeenCalledWith('info', { x: true });
  });

  it('always passes warn/error through, in every mode, forwarding all args', async () => {
    vi.stubEnv('DEV', false);
    vi.stubEnv('MODE', 'test');
    const logger = await loadLogger();

    const err = new Error('boom');
    logger.warn('careful', 42);
    logger.error('failed:', err);

    expect(console.warn).toHaveBeenCalledWith('careful', 42);
    expect(console.error).toHaveBeenCalledWith('failed:', err);
  });
});
