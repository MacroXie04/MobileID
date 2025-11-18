/**
 * Get user initials from name
 * @param {string} name - Full name
 * @returns {string} Initials (2 characters)
 */
export function getInitials(name) {
    if (!name) return 'U';

    const parts = name.trim().split(/\s+/);

    if (parts.length >= 2) {
        // Get first letter of first name and first letter of last name
        return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }

    // For single names, get first 2 characters
    return name.substring(0, 2).toUpperCase();
}

/**
 * Handle avatar image loading error
 * @param {Event} event - Image error event
 * @param {Object} options - Options
 * @param {string} options.profileName - User's name for fallback to initials
 * @param {string} options.placeholderSrc - Placeholder image URL
 * @param {Function} options.onShowInitials - Callback to show initials instead
 * @returns {void}
 */
export function handleAvatarError(event, options = {}) {
    const {profileName, placeholderSrc, onShowInitials} = options;

    // If we have a name and callback, show initials
    if (profileName && onShowInitials) {
        onShowInitials();
    } else if (placeholderSrc && event.target) {
        // Otherwise use placeholder image
        event.target.src = placeholderSrc;
    }
}

/**
 * Generate a deterministic color for user based on name
 * Useful for consistent avatar background colors
 * @param {string} name - User's name
 * @returns {string} HSL color string
 */
export function getAvatarColor(name) {
    if (!name) {
        return 'hsl(200, 50%, 50%)'; // Default blue-ish color
    }

    // Simple hash function to generate consistent number from name
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
        hash = hash & hash; // Convert to 32-bit integer
    }

    // Generate hue from hash (0-360)
    const hue = Math.abs(hash % 360);

    // Use consistent saturation and lightness for Material Design feel
    return `hsl(${hue}, 50%, 50%)`;
}

/**
 * Format user display name
 * @param {string} name - Full name
 * @param {number} maxLength - Maximum length (default: 30)
 * @returns {string} Formatted name
 */
export function formatDisplayName(name, maxLength = 30) {
    if (!name) return 'User';

    const trimmed = name.trim();

    if (trimmed.length <= maxLength) {
        return trimmed;
    }

    // Truncate with ellipsis
    return `${trimmed.substring(0, maxLength - 3)}...`;
}

/**
 * Validate and sanitize profile data
 * @param {Object} profile - Profile data
 * @returns {Object} Sanitized profile
 */
export function sanitizeProfile(profile) {
    if (!profile || typeof profile !== 'object') {
        return {
            name: 'User',
            information_id: 'ID not available'
        };
    }

    return {
        name: profile.name?.trim() || 'User',
        information_id: profile.information_id?.trim() || 'ID not available'
    };
}
