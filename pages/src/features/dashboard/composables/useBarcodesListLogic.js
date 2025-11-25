export function useBarcodesListLogic() {
  function iconForType(type) {
    if (type === 'DynamicBarcode') return 'qr_code_2';
    if (type === 'Identification') return 'badge';
    return 'barcode';
  }

  function getBarcodeDisplayTitle(barcodeType) {
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

  function getBarcodeTypeLabel(type) {
    if (type === 'DynamicBarcode') return 'Dynamic';
    if (type === 'Identification') return 'Identification';
    return 'Static';
  }

  function getProfileLabel(barcode) {
    if (!barcode.profile_info) return 'Profile';
    const { name, information_id, has_avatar } = barcode.profile_info;
    if (name && name.length <= 15) return name;
    if (information_id) {
      if (information_id.length > 8 && /^\d+$/.test(information_id))
        return `ID: ${information_id.slice(-4)}`;
      return `ID: ${information_id}`;
    }
    return has_avatar ? 'Profile+' : 'Profile';
  }

  function getProfileTooltip(barcode) {
    if (!barcode.profile_info) return 'Profile attached';
    const { name, information_id, has_avatar } = barcode.profile_info;
    const parts = [];
    if (name) parts.push(`Name: ${name}`);
    if (information_id) parts.push(`ID: ${information_id}`);
    if (has_avatar) parts.push('Has avatar image');
    return parts.length ? parts.join('\n') : 'Profile attached';
  }

  function getBarcodeDisplayId(barcode) {
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

  function formatRelativeTime(dateStr) {
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

  return {
    iconForType,
    getBarcodeDisplayTitle,
    getBarcodeTypeLabel,
    getProfileLabel,
    getProfileTooltip,
    getBarcodeDisplayId,
    formatRelativeTime,
  };
}
