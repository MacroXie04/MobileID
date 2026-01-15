import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { formatDate, formatRelativeTime, normalize } from '@shared/utils/common/dateUtils.js';

describe('date utils', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-15T12:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('formats relative time for recent moments', () => {
    const now = new Date();

    expect(formatRelativeTime(new Date(now.getTime() - 10_000).toISOString())).toBe('Just now');
    expect(formatRelativeTime(new Date(now.getTime() - 60_000).toISOString())).toBe('1 min ago');
    expect(formatRelativeTime(new Date(now.getTime() - 5 * 60_000).toISOString())).toBe('5 mins ago');
    expect(formatRelativeTime(new Date(now.getTime() - 2 * 3_600_000).toISOString())).toBe(
      '2 hours ago'
    );
    expect(formatRelativeTime(new Date(now.getTime() - 86_400_000).toISOString())).toBe('1 day ago');
  });

  it('falls back to locale date for older timestamps', () => {
    const oldDate = new Date('2025-12-01T10:00:00.000Z');
    expect(formatRelativeTime(oldDate.toISOString())).toBe(oldDate.toLocaleDateString());
  });

  it('formats date and time using locale output', () => {
    const dateStr = '2026-01-01T08:30:15.000Z';
    const expected = `${new Date(dateStr).toLocaleDateString()} ${new Date(
      dateStr
    ).toLocaleTimeString()}`;
    expect(formatDate(dateStr)).toBe(expected);
  });

  it('normalizes strings safely', () => {
    expect(normalize('TeSt')).toBe('test');
    expect(normalize(123)).toBe('123');
    expect(normalize(null)).toBe('');
  });
});
