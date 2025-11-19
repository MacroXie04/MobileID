/**
 * Validates an image file for type and size
 * @param {File} file - The file to validate
 * @param {Object} options - Validation options
 * @param {RegExp} options.allowedTypes - Regex for allowed MIME types (default: JPG, PNG, GIF, WebP)
 * @param {number} options.maxSizeMB - Maximum file size in MB (default: 5)
 * @returns {Object} Result with success status and error message
 */
export function validateImageFile(file, options = {}) {
    const {
        allowedTypes = /^image\/(jpe?g|png|gif|webp)$/i,
        maxSizeMB = 5
    } = options;

    if (!file) {
        return {success: false, error: 'No file selected'};
    }

    // Validate file type
    if (!allowedTypes.test(file.type)) {
        return {success: false, error: 'Please select a JPG, PNG, GIF, or WebP image'};
    }

    // Validate file size
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
        return {success: false, error: `Image size must be less than ${maxSizeMB}MB`};
    }

    return {success: true};
}

/**
 * Convert a File or Blob to base64 string
 * @param {File|Blob} file - The file to convert
 * @param {boolean} removePrefix - Whether to remove the data:image prefix (default: true)
 * @returns {Promise<string>} Base64 string
 */
export async function fileToBase64(file, removePrefix = true) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            const result = reader.result;
            if (removePrefix) {
                // Remove "data:image/jpeg;base64," prefix
                const base64 = result.split(',')[1];
                resolve(base64);
            } else {
                resolve(result);
            }
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

/**
 * Create a temporary object URL for a file
 * Automatically revokes previous URL if provided
 * @param {File|Blob} file - The file to create URL for
 * @param {string|null} previousUrl - Previous URL to revoke (optional)
 * @returns {string} Object URL
 */
export function createImageObjectURL(file, previousUrl = null) {
    if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
    }
    return URL.createObjectURL(file);
}

/**
 * Load image and get dimensions
 * @param {string} url - Image URL to load
 * @returns {Promise<Object>} Object containing width and height
 */
export async function getImageDimensions(url) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            resolve({width: img.width, height: img.height});
        };
        img.onerror = reject;
        img.src = url;
    });
}

/**
 * Check if image dimensions are within limits
 * @param {string} url - Image URL
 * @param {Object} options - Dimension limits
 * @param {number} options.minWidth - Minimum width (optional)
 * @param {number} options.minHeight - Minimum height (optional)
 * @param {number} options.maxWidth - Maximum width (optional)
 * @param {number} options.maxHeight - Maximum height (optional)
 * @returns {Promise<Object>} Result with success status and error message
 */
export async function validateImageDimensions(url, options = {}) {
    try {
        const {width, height} = await getImageDimensions(url);
        const {minWidth, minHeight, maxWidth, maxHeight} = options;

        if (minWidth && width < minWidth) {
            return {success: false, error: `Image width must be at least ${minWidth}px`};
        }
        if (minHeight && height < minHeight) {
            return {success: false, error: `Image height must be at least ${minHeight}px`};
        }
        if (maxWidth && width > maxWidth) {
            return {success: false, error: `Image width must be at most ${maxWidth}px`};
        }
        if (maxHeight && height > maxHeight) {
            return {success: false, error: `Image height must be at most ${maxHeight}px`};
        }

        return {success: true, dimensions: {width, height}};
    } catch (error) {
        return {success: false, error: 'Failed to load image'};
    }
}
