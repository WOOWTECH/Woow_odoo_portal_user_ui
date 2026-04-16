/**
 * Test Suite 06: Edge Cases & Stability
 *
 * Tests:
 * - Module cards with 0 count hidden
 * - MDI icon replacement correctness
 * - Logo link rewrite on portal pages
 * - Multiple rapid searches (debounce)
 * - Notification page with different tabs
 * - Empty notification state display
 * - Portal page accessible after login
 * - Admin vs portal user differences
 * - CSS variables fallback chain
 * - No JavaScript console errors
 */

const { chromium } = require('playwright');
const C = require('./config');

(async () => {
    console.log('\n>>> Test Suite 06: Edge Cases & Stability <<<\n');
    C.resetCounters();

    const browser = await chromium.launch({ headless: true });

    // ─── Group A: Module Card Behavior ───
    const ctx = await browser.newContext({ viewport: C.MOBILE_VP });
    const page = await ctx.newPage();

    // Capture console errors
    const consoleErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
        }
    });
    page.on('pageerror', err => {
        consoleErrors.push(err.message);
    });

    await C.loginAndNavigate(page, C.PORTAL_USER, '/my/home');
    // Extra wait for spinner to complete and hideEmptyModuleCards to run
    await page.waitForTimeout(5000);

    // A1: Cards with count 0 are hidden
    const zeroCountCards = await page.evaluate(() => {
        const cards = document.querySelectorAll('.o_portal_index_card[data-placeholder_count]');
        const results = [];
        cards.forEach(c => {
            const count = c.getAttribute('data-placeholder_count');
            const hidden = c.classList.contains('d-none');
            results.push({ count, hidden });
        });
        return results;
    });
    const zeroCards = zeroCountCards.filter(c => c.count === '0' || c.count === '');
    const allZeroHidden = zeroCards.every(c => c.hidden);
    if (zeroCards.length > 0) {
        C.assert(
            allZeroHidden,
            `A1: All 0-count module cards are hidden (${zeroCards.length} cards)`
        );
    } else {
        C.skip('A1: Zero-count cards hidden', 'no zero-count cards found');
    }

    // A2: MDI icon replacement — icons src should be custom MDI SVGs
    const iconSrcs = await page.evaluate(() => {
        // Check masked icon spans for mask-image URLs
        const spans = document.querySelectorAll('.o_portal_my_home .wpe-masked-icon');
        const srcs = [];
        spans.forEach(s => {
            const mask = s.style.webkitMaskImage || s.style.maskImage || '';
            srcs.push(mask);
        });
        return srcs;
    });
    const hasMdiIcons = iconSrcs.some(src => src.includes('woow_portal_enhanced'));
    if (iconSrcs.length > 0) {
        C.assert(
            hasMdiIcons,
            `A2: Some icons use custom MDI SVGs from woow_portal_enhanced (${iconSrcs.length} icons)`
        );
    } else {
        C.skip('A2: MDI icon replacement', 'no masked icons found');
    }

    // A3: Logo link rewrite (already tested but verify edge case — non-/my page)
    const logoOnHome = await page.evaluate(() => {
        const brand = document.querySelector('a.navbar-brand');
        return brand ? brand.getAttribute('href') : null;
    });
    C.assert(
        logoOnHome === '/my/home',
        `A3: Logo href on /my/home is "/my/home" (got: ${logoOnHome})`
    );

    // ─── Group B: Rapid Search Debounce ───
    const searchExists = await page.evaluate(() => !!document.querySelector('#wpe_module_search'));
    if (searchExists) {
        // Type rapidly without waiting for debounce
        await page.click('#wpe_module_search');
        await page.keyboard.type('abc', { delay: 20 });
        // Then clear by selecting all + delete
        await page.keyboard.press('Control+a');
        await page.keyboard.press('Backspace');
        await page.waitForTimeout(C.WAIT.DEBOUNCE + 200);

        // After clearing, all cards should be visible again
        const allVisible = await page.evaluate(() => {
            const cards = document.querySelectorAll('.o_portal_index_card:not(.d-none)');
            let hidden = 0;
            cards.forEach(c => {
                if (c.classList.contains('wpe-hidden')) hidden++;
            });
            return hidden;
        });
        C.assert(
            allVisible === 0,
            `B1: Rapid search + clear leaves no cards filtered (${allVisible} still hidden)`
        );
    } else {
        C.skip('B1: Rapid search debounce', 'no search input');
    }

    // ─── Group C: Notification Page Tabs ───
    await page.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await page.waitForTimeout(C.WAIT.PAGE_LOAD);

    // C1: All tabs have valid hrefs
    const tabInfo = await page.evaluate(() => {
        const tabs = document.querySelectorAll('.wpe-notif-tab');
        return Array.from(tabs).map(t => ({
            text: t.textContent.trim(),
            href: t.getAttribute('href'),
        }));
    });
    const allTabsHaveHref = tabInfo.every(t => t.href && t.href.startsWith('/my/notifications'));
    C.assert(
        tabInfo.length > 0 && allTabsHaveHref,
        `C1: All ${tabInfo.length} tabs have valid /my/notifications hrefs`
    );

    // C2: Navigate to each tab and verify page loads
    for (let i = 0; i < Math.min(tabInfo.length, 4); i++) {
        const tabHref = tabInfo[i].href;
        await page.goto(`${C.BASE_URL}${tabHref}`, { waitUntil: 'load' });
        await page.waitForTimeout(C.WAIT.PAGE_LOAD);

        const activeTab = await page.evaluate(() => {
            const active = document.querySelector('.wpe-notif-tab.active');
            return active ? active.textContent.trim() : null;
        });
        C.assert(
            activeTab !== null,
            `C2.${i + 1}: Tab "${tabInfo[i].text}" page loads with active tab "${activeTab}"`
        );
    }

    // ─── Group D: Console Errors ───
    // Filter out known harmless errors
    const realErrors = consoleErrors.filter(e =>
        !e.includes('favicon') &&
        !e.includes('writeText') &&
        !e.includes('clipboard') &&
        !e.includes('ResizeObserver') &&
        !e.includes('PerformanceObserver')
    );
    C.assert(
        realErrors.length === 0,
        `D1: No significant JavaScript console errors (found ${realErrors.length} errors${realErrors.length > 0 ? ': ' + realErrors[0].substring(0, 80) : ''})`
    );

    // ─── Group E: CSS Variable Fallback Chain ───
    const varFallback = await page.evaluate(() => {
        // Test that CSS variables resolve correctly
        const testEl = document.createElement('div');
        testEl.style.cssText = 'position:absolute;visibility:hidden;color:var(--custom-primary, var(--o-brand-primary, #714B67))';
        document.body.appendChild(testEl);
        const color = getComputedStyle(testEl).color;
        document.body.removeChild(testEl);
        return color;
    });
    C.assert(
        varFallback && varFallback !== 'rgb(0, 0, 0)' && varFallback.startsWith('rgb'),
        `E1: CSS variable fallback chain resolves (${varFallback})`
    );

    // ─── Group F: Multi-Page Footer Consistency ───
    const pagesToCheck = ['/my/home', '/my/orders', '/my/notifications'];
    for (const path of pagesToCheck) {
        await page.goto(`${C.BASE_URL}${path}`, { waitUntil: 'load' });
        await page.waitForTimeout(C.WAIT.PAGE_LOAD);

        const footerState = await page.evaluate(() => {
            const footer = document.querySelector('footer');
            if (!footer) return 'absent';
            return getComputedStyle(footer).display;
        });
        C.assert(
            footerState === 'absent' || footerState === 'none',
            `F1: Footer hidden on ${path} (state: ${footerState})`
        );
    }

    // ─── Group G: Admin User Check ───
    await ctx.close();
    const adminCtx = await browser.newContext({ viewport: C.MOBILE_VP });
    const adminPage = await adminCtx.newPage();
    await C.loginAndNavigate(adminPage, C.ADMIN_USER, '/my/home');

    // G1: Admin user can access portal home
    const adminTitle = await adminPage.title();
    C.assert(
        adminTitle.includes('Odoo'),
        `G1: Admin user can access portal home (title: ${adminTitle})`
    );

    // G2: Admin user also sees greeting card
    const adminGreeting = await adminPage.evaluate(() => {
        return !!document.querySelector('.wpe-greeting-card');
    });
    C.assert(
        adminGreeting,
        'G2: Admin user also sees greeting card on portal home'
    );

    // G3: Admin user has different notification access (might have more items)
    await adminPage.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await adminPage.waitForTimeout(C.WAIT.PAGE_LOAD);

    const adminNotifPage = await adminPage.evaluate(() => {
        return !!document.querySelector('.wpe-notif-tabs, #wpe_notif_list');
    });
    C.assert(
        adminNotifPage,
        'G3: Admin user can access notification page'
    );

    await adminCtx.close();
    await browser.close();

    C.printSummary('06: Edge Cases & Stability');
    process.exit(C.failCount > 0 ? 1 : 0);
})().catch(err => {
    console.error('FATAL:', err.message);
    process.exit(2);
});
