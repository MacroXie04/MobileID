import { config } from '@vue/test-utils';

config.global.stubs = {
  transition: false,
  'transition-group': false,
};

config.global.renderStubDefaultSlot = true;

const noop = () => {};

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
