/**
 * Test Suite 02: Color Customizer Integration
 *
 * Tests that all portal UI elements follow the active color customizer theme
 * (currently #2E86C1 blue). Covers:
 * - SVG icon mask-image tinting
 * - Dropdown menu icons follow theme
 * - Unread notification backgrounds use color-mix with primary
 * - Search bar focus ring uses primary color
 * - Notification card borders/shadows use primary
 * - Tab active state uses primary color
 * - Badge/dot colors follow primary
 */

const { chromium } = require('playwright');
const C = require('./config');

(async () => {
    console.log('\n>>> Test Suite 02: Color Customizer Integration <<<\n');
    C.resetCounters();

    const browser = await chromium.launch({ headless: true });
    const ctx = await browser.newContext({ viewport: C.MOBILE_VP });
    const page = await ctx.newPage();

    // ─── Group A: Portal Home - Icon Masking ───
    await C.loginAndNavigate(page, C.PORTAL_USER, '/my/home');

    // A1: Module card icons are replaced with wpe-masked-icon spans
    const maskedIcons = await page.evaluate(() => {
        const spans = document.querySelectorAll('.wpe-masked-icon');
        const results = [];
        spans.forEach(s => {
            const cs = getComputedStyle(s);
            results.push({
                bg: cs.backgroundColor,
                maskImage: cs.webkitMaskImage || cs.maskImage || '',
                width: s.offsetWidth,
                height: s.offsetHeight,
            });
        });
        return results;
    });
    C.assert(
        maskedIcons.length > 0,
        `A1: Found ${maskedIcons.length} masked icon spans (expected > 0)`
    );

    // A2: All masked icons use the theme primary color as background
    const allIconsThemed = maskedIcons.every(ic => C.colorsMatch(ic.bg, C.THEME_BLUE, 10));
    C.assert(
        allIconsThemed,
        `A2: All ${maskedIcons.length} masked icons have theme blue bg`
    );

    // A3: No leftover <img> in portal icon containers (should all be replaced)
    const leftoverImgs = await page.evaluate(() => {
        const imgs = document.querySelectorAll('.o_portal_icon img[src*=".svg"], .wpe-notification-icon img[src*=".svg"]');
        return imgs.length;
    });
    C.assert(
        leftoverImgs === 0,
        `A3: No leftover SVG <img> elements in icon containers (found: ${leftoverImgs})`
    );

    // A4: Masked icons have mask-image set
    const allHaveMask = maskedIcons.every(ic => ic.maskImage && ic.maskImage !== 'none' && ic.maskImage.length > 5);
    C.assert(
        allHaveMask,
        'A4: All masked icons have mask-image CSS property set'
    );

    // A5: Masked icons have reasonable dimensions (most should be non-zero)
    const iconsWithSize = maskedIcons.filter(ic => ic.width > 10 && ic.height > 10);
    C.assert(
        iconsWithSize.length > maskedIcons.length * 0.5,
        `A5: Most masked icons have non-zero dimensions (${iconsWithSize.length}/${maskedIcons.length} have size > 10px)`
    );

    // ─── Group B: Notification Preview Card Icons ───
    const previewIcons = await page.evaluate(() => {
        const spans = document.querySelectorAll('.wpe-notification-preview .wpe-masked-icon');
        return spans.length;
    });
    // Preview icons may not exist if there are no notifications
    if (previewIcons > 0) {
        C.assert(true, `B1: Notification preview icons also use mask approach (${previewIcons} found)`);
    } else {
        C.skip('B1: Notification preview icons mask approach', 'no preview notifications to test');
    }

    // ─── Group C: Dropdown Menu Colors ───
    // Open user dropdown
    const hasDropdown = await page.evaluate(() => !!document.querySelector('.dropdown-toggle.nav-link'));
    if (hasDropdown) {
        await page.click('.dropdown-toggle.nav-link');
        await page.waitForTimeout(C.WAIT.SHORT);

        const dropdownIcons = await page.evaluate(() => {
            const icons = document.querySelectorAll('.dropdown-menu .dropdown-item i.fa, .dropdown-menu .dropdown-item .oi');
            const results = [];
            icons.forEach(ic => {
                results.push({
                    classes: ic.className,
                    color: getComputedStyle(ic).color,
                });
            });
            return results;
        });

        C.assert(
            dropdownIcons.length > 0,
            `C1: Found ${dropdownIcons.length} dropdown menu icons`
        );

        // C2: Dropdown icons follow theme primary color
        const themedDropdownIcons = dropdownIcons.filter(ic =>
            ic.classes.includes('text-primary') || ic.classes.includes('text-primary-emphasis')
        );
        const allDropdownThemed = themedDropdownIcons.every(ic => C.colorsMatch(ic.color, C.THEME_BLUE, 15));
        C.assert(
            themedDropdownIcons.length === 0 || allDropdownThemed,
            `C2: Dropdown .text-primary icons follow theme color (${themedDropdownIcons.length} icons checked)`
        );

        // Close dropdown
        await page.click('body', { position: { x: 10, y: 10 } });
        await page.waitForTimeout(C.WAIT.SHORT);
    } else {
        C.skip('C1: Dropdown menu icons', 'no dropdown found');
        C.skip('C2: Dropdown icons theme color', 'no dropdown found');
    }

    // ─── Group D: Notification Page Colors ───
    await page.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await page.waitForTimeout(C.WAIT.PAGE_LOAD);

    // D1: Notification card icons use mask approach
    const notifMasked = await page.evaluate(() => {
        const spans = document.querySelectorAll('.wpe-notif-card-icon .wpe-masked-icon');
        const results = [];
        spans.forEach(s => {
            results.push({ bg: getComputedStyle(s).backgroundColor });
        });
        return results;
    });
    if (notifMasked.length > 0) {
        C.assert(true, `D1: Found ${notifMasked.length} notification card masked icons`);

        const allNotifThemed = notifMasked.every(ic => C.colorsMatch(ic.bg, C.THEME_BLUE, 10));
        C.assert(
            allNotifThemed,
            'D2: All notification card icons follow theme color'
        );
    } else {
        C.skip('D1: Notification card masked icons', 'no notification cards found');
        C.skip('D2: Notification card icon colors', 'no notification cards found');
    }

    // D3: Active tab has primary color
    const activeTab = await page.evaluate(() => {
        const tab = document.querySelector('.wpe-notif-tab.active');
        if (!tab) return null;
        return {
            color: getComputedStyle(tab).color,
            borderColor: getComputedStyle(tab).borderBottomColor,
        };
    });
    if (activeTab) {
        C.assert(
            C.colorsMatch(activeTab.color, C.THEME_BLUE, 20) ||
            C.colorsMatch(activeTab.borderColor, C.THEME_BLUE, 20),
            `D3: Active tab uses theme primary color (text: ${activeTab.color}, border: ${activeTab.borderColor})`
        );
    } else {
        C.skip('D3: Active tab primary color', 'no active tab found');
    }

    // D4: Unread dots use primary color
    const unreadDots = await page.evaluate(() => {
        const dots = document.querySelectorAll('.wpe-unread-dot:not(.d-none)');
        const results = [];
        dots.forEach(d => {
            results.push({ bg: getComputedStyle(d).backgroundColor });
        });
        return results;
    });
    if (unreadDots.length > 0) {
        const allDotsThemed = unreadDots.every(d => C.colorsMatch(d.bg, C.THEME_BLUE, 15));
        C.assert(
            allDotsThemed,
            `D4: Unread dots use theme primary color (${unreadDots.length} dots)`
        );
    } else {
        C.skip('D4: Unread dots primary color', 'no visible unread dots');
    }

    // D5: Unread cards have themed background (color-mix result)
    const unreadCards = await page.evaluate(() => {
        const cards = document.querySelectorAll('.wpe-notif-unread');
        const results = [];
        cards.forEach(c => {
            results.push({ bg: getComputedStyle(c).backgroundColor });
        });
        return results;
    });
    if (unreadCards.length > 0) {
        // The background should NOT be pure white — it should have a tinted color
        const allTinted = unreadCards.every(c => !C.colorsMatch(c.bg, C.WHITE, 5));
        C.assert(
            allTinted,
            `D5: Unread cards have tinted background (not pure white) — ${unreadCards.length} cards`
        );
    } else {
        C.skip('D5: Unread cards tinted background', 'no unread cards found');
    }

    // ─── Group E: CSS Custom Properties Verification ───
    const cssVars = await page.evaluate(() => {
        const root = document.documentElement;
        const cs = getComputedStyle(root);
        return {
            customPrimary: cs.getPropertyValue('--custom-primary').trim(),
            oBrandPrimary: cs.getPropertyValue('--o-brand-primary').trim(),
        };
    });
    C.assert(
        cssVars.customPrimary.length > 0 || cssVars.oBrandPrimary.length > 0,
        `E1: Theme CSS variable defined (--custom-primary: "${cssVars.customPrimary}", --o-brand-primary: "${cssVars.oBrandPrimary}")`
    );

    // E2: No hardcoded #714B67 in computed styles of key elements
    const hardcodedPurple = await page.evaluate(() => {
        const elements = document.querySelectorAll('.wpe-masked-icon, .wpe-unread-dot, .wpe-notif-tab.active');
        let found = 0;
        elements.forEach(el => {
            const cs = getComputedStyle(el);
            if (cs.color === 'rgb(113, 75, 103)' || cs.backgroundColor === 'rgb(113, 75, 103)') {
                found++;
            }
        });
        return found;
    });
    C.assert(
        hardcodedPurple === 0,
        `E2: No hardcoded Odoo purple (#714B67) found in themed elements (found: ${hardcodedPurple})`
    );

    await ctx.close();
    await browser.close();

    C.printSummary('02: Color Customizer Integration');
    process.exit(C.failCount > 0 ? 1 : 0);
})().catch(err => {
    console.error('FATAL:', err.message);
    process.exit(2);
});
