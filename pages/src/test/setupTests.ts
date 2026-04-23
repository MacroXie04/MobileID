import { config } from '@vue/test-utils';

config.global.stubs = {
  transition: false,
  'transition-group': false,
};

config.global.renderStubDefaultSlot = true;

const noop = () => {};

// Node.js 25+ exposes a broken globalThis.localStorage (no clear/setItem/etc.)
// that shadows jsdom 28's working implementation. Restore jsdom's version.
// @ts-expect-error vitest exposes jsdom instance on globalThis
const jsdomInstance = globalThis.jsdom;
if (jsdomInstance) {
  const jsdomWindow = jsdomInstance.window;
  for (const key of ['localStorage', 'sessionStorage'] as const) {
    if (
      typeof globalThis[key]?.clear !== 'function' &&
      typeof jsdomWindow[key]?.clear === 'function'
    ) {
      Object.defineProperty(globalThis, key, {
        value: jsdomWindow[key],
        writable: true,
        configurable: true,
      });
    }
  }
}

if (typeof window !== 'undefined') {
  if (!window.matchMedia) {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: (query) => ({
        media: query,
        matches: false,
        addEventListener: noop,
        removeEventListener: noop,
        addListener: noop,
        removeListener: noop,
        dispatchEvent: () => false,
        onchange: null,
      }),
    });
  }

  if (!window.ResizeObserver) {
    class MockResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }

    // @ts-expect-error jsdom does not implement ResizeObserver
    window.ResizeObserver = MockResizeObserver;
  }
}

export {};
