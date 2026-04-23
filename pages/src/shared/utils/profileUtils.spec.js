import { describe, expect, it, vi } from 'vitest';
import {
  formatDisplayName,
  getAvatarColor,
  getInitials,
  handleAvatarError,
  sanitizeProfile,
} from '@shared/utils/profileUtils.js';

describe('profile utils', () => {
  it('derives initials from names', () => {
    expect(getInitials('John Doe')).toBe('JD');
    expect(getInitials('Madonna')).toBe('MA');
    expect(getInitials('  John   Middle Doe  ')).toBe('JD');
    expect(getInitials('')).toBe('U');
  });

  it('handles avatar errors by showing initials when configured', () => {
    const onShowInitials = vi.fn();
    const event = { target: { src: 'before.png' } };

    handleAvatarError(event, { profileName: 'Jane Doe', onShowInitials });

    expect(onShowInitials).toHaveBeenCalledTimes(1);
    expect(event.target.src).toBe('before.png');
  });

  it('handles avatar errors with a placeholder image', () => {
    const event = { target: { src: 'before.png' } };

    handleAvatarError(event, { placeholderSrc: 'placeholder.png' });

    expect(event.target.src).toBe('placeholder.png');
  });

  it('generates deterministic avatar colors', () => {
    expect(getAvatarColor('')).toBe('hsl(200, 50%, 50%)');
    expect(getAvatarColor('Jane Doe')).toMatch(/^hsl\(\d{1,3}, 50%, 50%\)$/);
    expect(getAvatarColor('Jane Doe')).toBe(getAvatarColor('Jane Doe'));
  });

  it('formats display names with trimming and truncation', () => {
    expect(formatDisplayName('')).toBe('User');
    expect(formatDisplayName('  Jane Doe  ')).toBe('Jane Doe');
    expect(formatDisplayName('Very Long Display Name', 10)).toBe('Very Lo...');
  });

  it('sanitizes profile data safely', () => {
    expect(sanitizeProfile(null)).toEqual({
      name: 'User',
      information_id: 'ID not available',
    });

    expect(
      sanitizeProfile({
        name: '  Jane Doe  ',
        information_id: '  12345 ',
      })
    ).toEqual({
      name: 'Jane Doe',
      information_id: '12345',
    });

    expect(
      sanitizeProfile({
        name: '',
        information_id: '',
      })
    ).toEqual({
      name: 'User',
      information_id: 'ID not available',
    });
  });
});
