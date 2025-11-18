/**
 * jQuery Animation Utilities
 * Provides wrappers around jQuery animations for better code organization
 * Note: Requires jQuery to be loaded globally (window.$)
 */

/**
 * Fade in an element
 * @param {string} selector - jQuery selector
 * @param {number} duration - Animation duration in ms (default: 400)
 * @returns {Promise} Resolves when animation completes
 */
export function fadeIn(selector, duration = 400) {
    if (!window.$) {
        console.warn('jQuery not loaded');
        return Promise.resolve();
    }

    return new Promise((resolve) => {
        window.$(selector).fadeIn(duration, resolve);
    });
}

/**
 * Fade out an element
 * @param {string} selector - jQuery selector
 * @param {number} duration - Animation duration in ms (default: 400)
 * @returns {Promise} Resolves when animation completes
 */
export function fadeOut(selector, duration = 400) {
    if (!window.$) {
        console.warn('jQuery not loaded');
        return Promise.resolve();
    }

    return new Promise((resolve) => {
        window.$(selector).fadeOut(duration, resolve);
    });
}

/**
 * Set CSS properties on an element
 * @param {string} selector - jQuery selector
 * @param {Object} properties - CSS properties to set
 */
export function setCss(selector, properties) {
    if (!window.$) {
        console.warn('jQuery not loaded');
        return;
    }

    window.$(selector).css(properties);
}

/**
 * Get CSS property value
 * @param {string} selector - jQuery selector
 * @param {string} property - CSS property name
 * @returns {string} Property value
 */
export function getCss(selector, property) {
    if (!window.$) {
        console.warn('jQuery not loaded');
        return '';
    }

    return window.$(selector).css(property);
}

/**
 * Check if element is visible
 * @param {string} selector - jQuery selector
 * @returns {boolean} True if visible
 */
export function isVisible(selector) {
    if (!window.$) {
        console.warn('jQuery not loaded');
        return false;
    }

    return window.$(selector).css('display') !== 'none';
}

/**
 * Animate barcode display sequence for School view
 * Handles the complete show/hide sequence with progress bar
 * @param {Object} options - Configuration
 * @param {number} options.displayDuration - Duration to show barcode in ms (default: 10000)
 * @param {number} options.fadeInDuration - Fade in duration in ms (default: 400)
 * @param {number} options.fadeOutDuration - Fade out duration in ms (default: 400)
 * @returns {Promise} Resolves when sequence completes
 */
export async function animateBarcodeSequence(options = {}) {
    const {
        displayDuration = 10000,
        fadeInDuration = 400,
        fadeOutDuration = 400
    } = options;

    if (!window.$) {
        console.warn('jQuery not loaded');
        return;
    }

    const isFaded = getCss('#show-info-button', 'display') === 'none';

    if (isFaded) {
        // Show button, hide other elements
        await fadeOut('#information_id');
        await fadeOut('#qrcode-code');
        await fadeOut('#qrcode-div');
        await new Promise(resolve => setTimeout(resolve, fadeInDuration));
        await fadeIn('#show-info-button');
    } else {
        // Hide button, show barcode elements
        await fadeOut('#show-info-button');

        await new Promise(resolve => setTimeout(resolve, fadeInDuration));

        // Show barcode elements
        await Promise.all([
            fadeIn('#qrcode-div'),
            fadeIn('#qrcode-code'),
            fadeIn('#information_id')
        ]);

        // Reset progress bar
        setCss('.progress-bar', {
            transition: 'none',
            width: '100%'
        });

        // Apply transition after short delay
        await new Promise(resolve => setTimeout(resolve, 50));
        setCss('.progress-bar', {
            transition: `width ${displayDuration}ms linear`,
            width: '0%'
        });

        // Wait for display duration
        await new Promise(resolve => setTimeout(resolve, displayDuration + fadeOutDuration));

        // Hide barcode elements
        await Promise.all([
            fadeOut('#qrcode-div', fadeOutDuration),
            fadeOut('#qrcode-code', fadeOutDuration),
            fadeOut('#information_id', fadeOutDuration)
        ]);

        await new Promise(resolve => setTimeout(resolve, fadeOutDuration));

        // Show button again
        await fadeIn('#show-info-button');
    }
}

/**
 * Simple wrapper for multiple jQuery animations in sequence
 * @param {Array<Function>} animations - Array of animation functions
 * @returns {Promise} Resolves when all animations complete
 */
export async function runSequence(animations) {
    for (const animation of animations) {
        await animation();
    }
}

/**
 * Simple wrapper for multiple jQuery animations in parallel
 * @param {Array<Function>} animations - Array of animation functions
 * @returns {Promise} Resolves when all animations complete
 */
export async function runParallel(animations) {
    await Promise.all(animations.map(animation => animation()));
}
