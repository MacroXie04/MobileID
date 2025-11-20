import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import UserProfile from '../UserProfile.vue'

describe('UserProfile', () => {
    const mockProfile = {
        name: 'John Doe',
        information_id: '12345'
    }

    it('renders user name and id correctly', () => {
        const wrapper = mount(UserProfile, {
            props: {
                profile: mockProfile
            }
        })

        expect(wrapper.find('.user-name').text()).toBe('John Doe')
        expect(wrapper.find('.user-id').text()).toBe('12345')
    })

    it('renders default name and id when profile is missing', () => {
        const wrapper = mount(UserProfile, {
            props: {
                profile: {}
            }
        })

        expect(wrapper.find('.user-name').text()).toBe('User')
        expect(wrapper.find('.user-id').text()).toBe('ID not available')
    })

    it('renders avatar image when avatarSrc is provided', () => {
        const avatarSrc = 'https://example.com/avatar.png'
        const wrapper = mount(UserProfile, {
            props: {
                profile: mockProfile,
                avatarSrc
            }
        })

        const img = wrapper.find('img.avatar-image')
        expect(img.exists()).toBe(true)
        expect(img.attributes('src')).toBe(avatarSrc)
    })

    it('renders initials when avatarSrc is not provided', () => {
        const wrapper = mount(UserProfile, {
            props: {
                profile: mockProfile,
                avatarSrc: ''
            }
        })

        expect(wrapper.find('.avatar-initials').exists()).toBe(true)
        expect(wrapper.find('.avatar-initials').text()).toBe('JD')
    })
})
