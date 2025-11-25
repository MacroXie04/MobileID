/**
 * Date and time formatting utilities
 */

/**
 * Format a date string as relative time (e.g., "2 hours ago", "3 days ago")
 * @param {string} dateStr - ISO date string
 * @returns {string} - Formatted relative time string
 */
export function formatRelativeTime(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

  return date.toLocaleDateString();
}

/**
 * Format a date string as full date and time
 * @param {string} dateStr - ISO date string
 * @returns {string} - Formatted date and time string
 */
export function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Normalize a string to lowercase for comparison
 * @param {any} str - String to normalize
 * @returns {string} - Lowercase string or empty string on error
 */
export function normalize(str) {
  try {
    return String(str || '').toLowerCase();
  } catch {
    return '';
  }
}
