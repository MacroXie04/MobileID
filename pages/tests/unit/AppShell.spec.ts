import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import App from '@/App.vue';

describe('App shell', () => {
  it('renders the router outlet shell', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          'router-view': {
            template: '<div data-test="router-view-placeholder" />',
          },
        },
      },
    });

    expect(wrapper.find('[data-test="router-view-placeholder"]').exists()).toBe(true);
  });
});

