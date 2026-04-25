import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';

import UserProfile from '@mobile-id/components/user-profile/UserProfile.vue';

const mockHandleGenerate = vi.fn();

vi.mock('@mobile-id/components/user-profile/UserProfile.setup', () => ({
  emitsDefinition: ['generate'],
  propsDefinition: {
    profile: {
      type: Object,
      required: true,
    },
    avatarSrc: {
      type: String,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    barcodeVisible: {
      type: Boolean,
      default: false,
    },
    isRefreshingToken: {
      type: Boolean,
      default: false,
    },
  },
  useSchoolUserProfileSetup: () => ({
    shouldShowAvatar: false,
    getInitials: () => 'TU',
    handleImageError: vi.fn(),
    handleGenerate: mockHandleGenerate,
  }),
}));

describe('School UserProfile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows the pay button before barcode display and swaps to the information id when barcode is visible', async () => {
    const wrapper = mount(UserProfile, {
      props: {
        profile: {
          name: 'Test User',
          information_id: 'ID-123',
        },
        avatarSrc: '',
        barcodeVisible: false,
      },
    });

    expect(wrapper.get('#show-info-button').attributes('aria-hidden')).toBe('false');
    expect(wrapper.get('#information_id').attributes('aria-hidden')).toBe('true');

    await wrapper.setProps({ barcodeVisible: true });

    expect(wrapper.get('#show-info-button').attributes('aria-hidden')).toBe('true');
    expect(wrapper.get('#information_id').attributes('aria-hidden')).toBe('false');
    expect(wrapper.text()).toContain('ID-123');
  });
});
