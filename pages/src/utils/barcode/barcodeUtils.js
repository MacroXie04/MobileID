/**
 * Barcode formatting and display utilities
 */

/**
 * Get display title for barcode type
 * @param {string} barcodeType - Type of barcode
 * @returns {string} - Human-readable barcode type
 */
export function getBarcodeDisplayTitle(barcodeType) {
  switch (barcodeType) {
    case 'DynamicBarcode':
      return 'Dynamic Barcode';
    case 'Others':
      return 'Barcode';
    case 'Identification':
      return 'Identification Barcode';
    default:
      return 'Barcode';
  }
}

/**
 * Get display ID for a barcode (with masked digits)
 * @param {Object} barcode - Barcode object with barcode_type and barcode properties
 * @returns {string} - Formatted barcode display ID
 */
export function getBarcodeDisplayId(barcode) {
  switch (barcode.barcode_type) {
    case 'DynamicBarcode':
      return `Dynamic •••• ${barcode.barcode.slice(-4)}`;
    case 'Others':
      return `Barcode ending with ${barcode.barcode.slice(-4)}`;
    case 'Identification':
      return 'Identification Barcode';
    default:
      return `•••• ${barcode.barcode.slice(-4)}`;
  }
}

/**
 * Get short label for barcode type
 * @param {string} type - Barcode type
 * @returns {string} - Short label
 */
export function getBarcodeTypeLabel(type) {
  if (type === 'DynamicBarcode') return 'Dynamic';
  if (type === 'Identification') return 'Identification';
  return 'Static';
}

/**
 * Get display label for barcode profile
 * @param {Object} barcode - Barcode object with profile_info
 * @returns {string} - Profile label
 */
export function getProfileLabel(barcode) {
  if (!barcode.profile_info) return 'Profile';

  const { name, information_id, has_avatar } = barcode.profile_info;

  // Show name if available and not too long
  if (name && name.length <= 15) {
    return name;
  }

  // Show information ID if available and name is too long or not available
  if (information_id) {
    // Show last 4 digits if it's a long ID number
    if (information_id.length > 8 && /^\d+$/.test(information_id)) {
      return `ID: ${information_id.slice(-4)}`;
    }
    // Show full ID if it's short or contains letters
    return `ID: ${information_id}`;
  }

  // Fallback to generic label with avatar indicator
  return has_avatar ? 'Profile+' : 'Profile';
}

/**
 * Get tooltip text for barcode profile
 * @param {Object} barcode - Barcode object with profile_info
 * @returns {string} - Profile tooltip text
 */
export function getProfileTooltip(barcode) {
  if (!barcode.profile_info) return 'Profile attached';

  const { name, information_id, has_avatar } = barcode.profile_info;
  const parts = [];

  if (name) parts.push(`Name: ${name}`);
  if (information_id) parts.push(`ID: ${information_id}`);
  if (has_avatar) parts.push('Has avatar image');

  return parts.length ? parts.join('\n') : 'Profile attached';
}

/**
 * Get association status text
 * @param {boolean} isAssociated - Whether profile is associated with barcode
 * @returns {string} - Status text
 */
export function getAssociationStatusText(isAssociated) {
  if (isAssociated) {
    return 'Active - Profile associated with barcode';
  }
  return 'Inactive - No profile association';
}
