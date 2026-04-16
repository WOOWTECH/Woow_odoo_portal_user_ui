/**
 * Test Suite 01: Portal Layout & Navigation
 *
 * Tests:
 * - Navbar white background
 * - Navbar brand/logo link → /my/home
 * - Username visible (dark text) on navbar
 * - Breadcrumb bar white background
 * - Breadcrumb text dark color
 * - Back button present and functional
 * - Footer hidden on portal pages
 * - Greeting card displayed on home
 * - Mobile hamburger menu visible
 */

const { chromium } = require('playwright');
const C = require('./config');

(async () => {
    console.log('\n>>> Test Suite 01: Portal Layout & Navigation <<<\n');
    C.resetCounters();

    const browser = await chromium.launch({ headless: true });

    // ─── Test Group A: Mobile Layout (Portal Home) ───
    const mCtx = await browser.newContext({ viewport: C.MOBILE_VP });
    const mPage = await mCtx.newPage();
    await C.loginAndNavigate(mPage, C.PORTAL_USER, '/my/home');

    // A1: Navbar has white background
    const navBg = await mPage.evaluate(() => {
        const nav = document.querySelector('header .navbar, nav.navbar');
        return nav ? getComputedStyle(nav).backgroundColor : null;
    });
    C.assert(
        navBg && C.colorsMatch(navBg, C.WHITE, 10),
        'A1: Top navbar has white background'
    );

    // A2: Navbar username visible (dark text)
    const userLink = await mPage.evaluate(() => {
        const links = document.querySelectorAll('header .navbar .nav-link, header .navbar .dropdown-toggle');
        for (const el of links) {
            const text = el.textContent.trim();
            if (text && text.length > 1 && !text.match(/^(Home|Sign|Log)/i)) {
                return { text, color: getComputedStyle(el).color };
            }
        }
        return null;
    });
    C.assert(
        userLink && !C.colorsMatch(userLink.color, C.WHITE, 30),
        `A2: Username "${userLink?.text}" is NOT white (color: ${userLink?.color})`
    );

    // A3: Username has dark text
    C.assert(
        userLink && C.colorsMatch(userLink.color, C.DEEP_GRAY, 30),
        `A3: Username has dark/deep-gray text`
    );

    // A4: Logo link points to /my/home
    const logoHref = await mPage.evaluate(() => {
        const brand = document.querySelector('a.navbar-brand');
        return brand ? brand.getAttribute('href') : null;
    });
    C.assert(
        logoHref === '/my/home',
        `A4: Logo link href="/my/home" (got: ${logoHref})`
    );

    // A5: Greeting card is displayed
    const greetingCard = await mPage.evaluate(() => {
        const card = document.querySelector('.wpe-greeting-card');
        if (!card) return null;
        const cs = getComputedStyle(card);
        return {
            display: cs.display,
            hasAvatar: !!card.querySelector('.wpe-greeting-avatar'),
            hasName: !!card.querySelector('h4'),
        };
    });
    C.assert(
        greetingCard && greetingCard.display !== 'none',
        'A5: Greeting card is visible on portal home'
    );
    C.assert(
        greetingCard && greetingCard.hasAvatar,
        'A6: Greeting card has user avatar'
    );
    C.assert(
        greetingCard && greetingCard.hasName,
        'A7: Greeting card has user name heading'
    );

    // A8: Footer hidden
    const footerHome = await mPage.evaluate(() => {
        const footer = document.querySelector('footer');
        if (!footer) return { exists: false };
        return { exists: true, display: getComputedStyle(footer).display };
    });
    C.assert(
        !footerHome.exists || footerHome.display === 'none',
        `A8: Footer hidden on /my/home (display: ${footerHome.display})`
    );

    // A9: Mobile hamburger menu or user dropdown is accessible
    const hamburger = await mPage.evaluate(() => {
        // Odoo portal may use .navbar-toggler or just show the dropdown toggle
        const toggler = document.querySelector('.navbar-toggler');
        const dropdown = document.querySelector('.dropdown-toggle.nav-link');
        if (toggler) {
            const cs = getComputedStyle(toggler);
            return { type: 'hamburger', display: cs.display, visible: cs.display !== 'none' };
        }
        if (dropdown) {
            const cs = getComputedStyle(dropdown);
            return { type: 'dropdown', display: cs.display, visible: cs.display !== 'none' };
        }
        return null;
    });
    C.assert(
        hamburger && hamburger.visible,
        `A9: Mobile navigation accessible (${hamburger?.type}, display: ${hamburger?.display})`
    );

    // ─── Test Group B: Subpage Layout (Orders) ───
    await mPage.goto(`${C.BASE_URL}/my/orders`, { waitUntil: 'load' });
    await mPage.waitForTimeout(C.WAIT.PAGE_LOAD);

    // B1: Breadcrumb bar has white background
    const bcBg = await mPage.evaluate(() => {
        const nav = document.querySelector('.o_portal_navbar, nav.o_portal_navbar');
        return nav ? getComputedStyle(nav).backgroundColor : null;
    });
    C.assert(
        bcBg && C.colorsMatch(bcBg, C.WHITE, 15),
        `B1: Breadcrumb bar has white background (got: ${bcBg})`
    );

    // B2: Breadcrumb text is dark
    const bcText = await mPage.evaluate(() => {
        const item = document.querySelector('.o_portal_navbar .breadcrumb-item, .o_portal_navbar .breadcrumb-item a');
        return item ? getComputedStyle(item).color : null;
    });
    C.assert(
        bcText && !C.colorsMatch(bcText, C.WHITE, 30),
        `B2: Breadcrumb text is NOT white (color: ${bcText})`
    );

    // B3: Back button exists
    const backBtn = await mPage.evaluate(() => {
        const btn = document.querySelector('.wpe-breadcrumb-back-btn, .wpe-back-btn-item');
        if (!btn) return null;
        return { text: btn.textContent.trim(), display: getComputedStyle(btn).display };
    });
    C.assert(
        backBtn && backBtn.display !== 'none',
        `B3: Back button exists and visible (text: "${backBtn?.text}")`
    );

    // B4: Footer hidden on orders page
    const footerOrders = await mPage.evaluate(() => {
        const footer = document.querySelector('footer');
        if (!footer) return { exists: false };
        return { exists: true, display: getComputedStyle(footer).display };
    });
    C.assert(
        !footerOrders.exists || footerOrders.display === 'none',
        `B4: Footer hidden on /my/orders (display: ${footerOrders.display})`
    );

    // ─── Test Group C: Desktop Layout ───
    const dCtx = await browser.newContext({ viewport: C.DESKTOP_VP });
    const dPage = await dCtx.newPage();
    await C.loginAndNavigate(dPage, C.PORTAL_USER, '/my/home');

    // C1: Desktop - navbar brand visible
    const desktopBrand = await dPage.evaluate(() => {
        const brand = document.querySelector('a.navbar-brand');
        if (!brand) return null;
        const cs = getComputedStyle(brand);
        return { text: brand.textContent.trim(), color: cs.color, display: cs.display };
    });
    C.assert(
        desktopBrand && desktopBrand.display !== 'none',
        'C1: Desktop navbar brand is visible'
    );

    // C2: Desktop - greeting card constrained width
    const greetingWidth = await dPage.evaluate(() => {
        const card = document.querySelector('.wpe-greeting-card');
        if (!card) return null;
        return card.getBoundingClientRect().width;
    });
    C.assert(
        greetingWidth && greetingWidth <= 800,
        `C2: Greeting card has constrained width on desktop (${greetingWidth?.toFixed(0)}px)`
    );

    // C3: Desktop footer also hidden
    const footerDesktop = await dPage.evaluate(() => {
        const footer = document.querySelector('footer');
        if (!footer) return { exists: false };
        return { exists: true, display: getComputedStyle(footer).display };
    });
    C.assert(
        !footerDesktop.exists || footerDesktop.display === 'none',
        'C3: Footer hidden on desktop portal home'
    );

    await mCtx.close();
    await dCtx.close();
    await browser.close();

    C.printSummary('01: Layout & Navigation');
    process.exit(C.failCount > 0 ? 1 : 0);
})().catch(err => {
    console.error('FATAL:', err.message);
    process.exit(2);
});
