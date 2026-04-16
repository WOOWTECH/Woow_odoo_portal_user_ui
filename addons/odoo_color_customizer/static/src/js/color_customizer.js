/** @odoo-module **/
/**
 * Color Customizer - Live Preview JavaScript
 *
 * This module handles:
 * 1. Loading custom color CSS on application start
 * 2. Live preview when changing colors in settings
 * 3. Color manipulation utilities
 */

import { registry } from "@web/core/registry";

const COLOR_CSS_ID = 'color-customizer-theme';
const CSS_ENDPOINT = '/color_customizer/theme.css';

// =============================================================================
// Color Utilities
// =============================================================================

/**
 * Convert hex color to RGB object
 * @param {string} hex - Hex color (e.g., '#71639e')
 * @returns {Object|null} RGB object with r, g, b properties
 */
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

/**
 * Convert RGB values to hex color
 * @param {number} r - Red (0-255)
 * @param {number} g - Green (0-255)
 * @param {number} b - Blue (0-255)
 * @returns {string} Hex color string
 */
function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(x => {
        const hex = Math.max(0, Math.min(255, Math.round(x))).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

/**
 * Darken a hex color by a percentage
 * @param {string} hex - Hex color
 * @param {number} amount - Amount to darken (0.0 to 1.0)
 * @returns {string} Darkened hex color
 */
function darkenColor(hex, amount) {
    const rgb = hexToRgb(hex);
    if (!rgb) return hex;
    const factor = 1 - amount;
    return rgbToHex(rgb.r * factor, rgb.g * factor, rgb.b * factor);
}

/**
 * Lighten a hex color by a percentage
 * @param {string} hex - Hex color
 * @param {number} amount - Amount to lighten (0.0 to 1.0)
 * @returns {string} Lightened hex color
 */
function lightenColor(hex, amount) {
    const rgb = hexToRgb(hex);
    if (!rgb) return hex;
    return rgbToHex(
        rgb.r + (255 - rgb.r) * amount,
        rgb.g + (255 - rgb.g) * amount,
        rgb.b + (255 - rgb.b) * amount
    );
}

/**
 * Get contrasting text color (white or black) for background
 * @param {string} hex - Background hex color
 * @returns {string} '#ffffff' or '#000000'
 */
function getContrastColor(hex) {
    const rgb = hexToRgb(hex);
    if (!rgb) return '#ffffff';
    const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
    return luminance < 0.5 ? '#ffffff' : '#000000';
}

// =============================================================================
// Theme Loading
// =============================================================================

/**
 * Load custom color theme CSS from server
 * Injects a <style> tag with CSS from the controller endpoint
 */
async function loadColorTheme() {
    // Skip if already loaded
    if (document.getElementById(COLOR_CSS_ID)) {
        return;
    }

    try {
        // Add cache-busting parameter to ensure fresh CSS
        const cacheBuster = `?t=${Date.now()}`;
        const response = await fetch(CSS_ENDPOINT + cacheBuster, { cache: 'no-store' });
        if (response.ok) {
            const css = await response.text();
            const style = document.createElement('style');
            style.id = COLOR_CSS_ID;
            style.textContent = css;
            document.head.appendChild(style);
        }
    } catch (error) {
        console.warn('[ColorCustomizer] Could not load theme CSS:', error);
    }
}

/**
 * Refresh theme CSS from server (after settings change)
 */
async function refreshThemeCSS() {
    const existingStyle = document.getElementById(COLOR_CSS_ID);
    if (existingStyle) {
        existingStyle.remove();
    }
    // Clear inline styles
    clearInlineStyles();

    // Force reload with cache bypass
    try {
        const cacheBuster = `?t=${Date.now()}`;
        const response = await fetch(CSS_ENDPOINT + cacheBuster, { cache: 'no-store' });
        if (response.ok) {
            const css = await response.text();
            const style = document.createElement('style');
            style.id = COLOR_CSS_ID;
            style.textContent = css;
            document.head.appendChild(style);
        }
    } catch (error) {
        console.warn('[ColorCustomizer] Could not refresh theme CSS:', error);
    }
}

/**
 * Clear inline CSS variable styles
 */
function clearInlineStyles() {
    const root = document.documentElement;
    root.style.removeProperty('--custom-primary');
    root.style.removeProperty('--custom-primary-hover');
    root.style.removeProperty('--custom-primary-active');
    root.style.removeProperty('--custom-primary-light');
    root.style.removeProperty('--custom-primary-text');
}

// =============================================================================
// Live Preview
// =============================================================================

/**
 * Update CSS variables for live preview
 * @param {string} color - Hex color value
 */
function updateLivePreview(color) {
    // Validate hex color format
    if (!color || !color.match(/^#[0-9A-Fa-f]{6}$/)) {
        return;
    }

    const root = document.documentElement;
    root.style.setProperty('--custom-primary', color);
    root.style.setProperty('--custom-primary-hover', darkenColor(color, 0.1));
    root.style.setProperty('--custom-primary-active', darkenColor(color, 0.2));
    root.style.setProperty('--custom-primary-light', lightenColor(color, 0.85));
    root.style.setProperty('--custom-primary-text', getContrastColor(color));

    // Also update Odoo brand colors for immediate effect
    root.style.setProperty('--o-brand-odoo', color);
    root.style.setProperty('--o-brand-primary', color);
}

// =============================================================================
// Odoo Service Registration
// =============================================================================

/**
 * Color Customizer Service
 * Registered with Odoo's service registry to load theme on start
 */
const colorCustomizerService = {
    start() {
        // Load theme CSS on application start
        loadColorTheme();

        // Return API for other components to use
        return {
            updateLivePreview,
            refreshThemeCSS,
            loadColorTheme,
        };
    },
};

registry.category("services").add("colorCustomizer", colorCustomizerService);

// =============================================================================
// Global API & Event Listeners
// =============================================================================

// Expose globally for easy access from settings page
window.ColorCustomizer = {
    updateLivePreview,
    refreshThemeCSS,
    loadColorTheme,
};

// Listen for color input changes on settings page
document.addEventListener('input', (event) => {
    const target = event.target;
    if (target && target.name === 'primary_color' && target.type === 'color') {
        updateLivePreview(target.value);
    }
});

// Also listen for change events (for non-continuous updates)
document.addEventListener('change', (event) => {
    const target = event.target;
    if (target && target.name === 'primary_color') {
        updateLivePreview(target.value);
    }
});
