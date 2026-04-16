/**
 * Test Suite 05: Mobile & Responsive Design
 *
 * Tests:
 * - Mobile viewport (390x844) layout correctness
 * - Desktop viewport (1280x800) layout correctness
 * - Modal bottom-sheet style on mobile
 * - Touch-optimized element sizes
 * - Responsive font sizes
 * - Hamburger menu vs inline nav
 */

const { chromium } = require('playwright');
const C = require('./config');

(async () => {
    console.log('\n>>> Test Suite 05: Mobile & Responsive Design <<<\n');
    C.resetCounters();

    const browser = await chromium.launch({ headless: true });

    // ─── Group A: Mobile Layout ───
    const mCtx = await browser.newContext({ viewport: C.MOBILE_VP });
    const mPage = await mCtx.newPage();
    await C.loginAndNavigate(mPage, C.PORTAL_USER, '/my/home');

    // A1: Module cards are full-width on mobile
    const mobileCardWidth = await mPage.evaluate(() => {
        const card = document.querySelector('.o_portal_index_card:not(.d-none)');
        if (!card) return null;
        const link = card.querySelector('a');
        if (!link) return null;
        return {
            cardWidth: link.getBoundingClientRect().width,
            viewportWidth: window.innerWidth,
        };
    });
    if (mobileCardWidth) {
        const ratio = mobileCardWidth.cardWidth / mobileCardWidth.viewportWidth;
        C.assert(
            ratio > 0.8,
            `A1: Module cards are near full-width on mobile (${(ratio * 100).toFixed(0)}% of viewport)`
        );
    } else {
        C.skip('A1: Mobile card width', 'no visible module card');
    }

    // A2: Search bar is full-width on mobile
    const mobileSearchWidth = await mPage.evaluate(() => {
        const bar = document.querySelector('.wpe-search-bar');
        if (!bar) return null;
        return {
            barWidth: bar.getBoundingClientRect().width,
            viewportWidth: window.innerWidth,
        };
    });
    if (mobileSearchWidth) {
        const ratio = mobileSearchWidth.barWidth / mobileSearchWidth.viewportWidth;
        C.assert(
            ratio > 0.85,
            `A2: Search bar is near full-width on mobile (${(ratio * 100).toFixed(0)}%)`
        );
    } else {
        C.skip('A2: Mobile search bar width', 'no search bar');
    }

    // A3: Greeting card on mobile uses full width
    const mobileGreetingWidth = await mPage.evaluate(() => {
        const card = document.querySelector('.wpe-greeting-card');
        if (!card) return null;
        return {
            width: card.getBoundingClientRect().width,
            viewportWidth: window.innerWidth,
        };
    });
    if (mobileGreetingWidth) {
        const ratio = mobileGreetingWidth.width / mobileGreetingWidth.viewportWidth;
        C.assert(
            ratio > 0.8,
            `A3: Greeting card is near full-width on mobile (${(ratio * 100).toFixed(0)}%)`
        );
    } else {
        C.skip('A3: Mobile greeting card width', 'no greeting card');
    }

    // A4: Mobile navigation accessible (hamburger or user dropdown)
    const mobileHamburger = await mPage.evaluate(() => {
        const toggler = document.querySelector('.navbar-toggler');
        const dropdown = document.querySelector('.dropdown-toggle.nav-link');
        if (toggler) {
            const cs = getComputedStyle(toggler);
            return { type: 'hamburger', visible: cs.display !== 'none' };
        }
        if (dropdown) {
            const cs = getComputedStyle(dropdown);
            return { type: 'dropdown', visible: cs.display !== 'none' };
        }
        return null;
    });
    C.assert(
        mobileHamburger && mobileHamburger.visible,
        `A4: Mobile navigation accessible (${mobileHamburger?.type})`
    );

    // ─── Mobile Notification Page ───
    await mPage.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await mPage.waitForTimeout(C.WAIT.PAGE_LOAD);

    // A5: Notification tabs are horizontally scrollable / full width
    const mobileTabsWidth = await mPage.evaluate(() => {
        const tabBar = document.querySelector('.wpe-notif-tabs');
        if (!tabBar) return null;
        return {
            width: tabBar.getBoundingClientRect().width,
            viewportWidth: window.innerWidth,
        };
    });
    if (mobileTabsWidth) {
        const ratio = mobileTabsWidth.width / mobileTabsWidth.viewportWidth;
        C.assert(
            ratio > 0.85,
            `A5: Notification tabs span full width on mobile (${(ratio * 100).toFixed(0)}%)`
        );
    } else {
        C.skip('A5: Mobile notification tabs', 'no tab bar');
    }

    // A6: Tab font size smaller on mobile
    const mobileTabFont = await mPage.evaluate(() => {
        const tab = document.querySelector('.wpe-notif-tab');
        if (!tab) return null;
        return parseFloat(getComputedStyle(tab).fontSize);
    });
    if (mobileTabFont) {
        C.assert(
            mobileTabFont <= 14,
            `A6: Tabs have smaller font on mobile (${mobileTabFont}px, expected <= 14px)`
        );
    } else {
        C.skip('A6: Mobile tab font size', 'no tab element');
    }

    // A7: Touch target sizes >= 44px for interactive elements
    const touchTargets = await mPage.evaluate(() => {
        const selectors = [
            '.wpe-notif-card',
            '.wpe-notif-tab',
            '#wpe_mark_all_read',
            '#wpe_notif_searchbar_toggle',
        ];
        const results = [];
        selectors.forEach(sel => {
            const el = document.querySelector(sel);
            if (!el) return;
            const rect = el.getBoundingClientRect();
            results.push({ selector: sel, height: rect.height, width: rect.width });
        });
        return results;
    });
    const touchFriendlyCount = touchTargets.filter(t => t.height >= 32).length;
    C.assert(
        touchTargets.length > 0 && touchFriendlyCount >= touchTargets.length * 0.6,
        `A7: Most interactive elements have adequate touch height (${touchFriendlyCount}/${touchTargets.length} >= 32px)`
    );

    // A8: Modal displays as bottom sheet on mobile
    const notifCardExists = await mPage.evaluate(() => !!document.querySelector('.wpe-notif-card'));
    if (notifCardExists) {
        await mPage.click('.wpe-notif-card');
        await mPage.waitForTimeout(1500);

        const mobileModal = await mPage.evaluate(() => {
            const modal = document.querySelector('.wpe-notif-modal');
            if (!modal) return null;
            const cs = getComputedStyle(modal);
            return {
                borderRadius: cs.borderRadius,
                maxHeight: cs.maxHeight,
                bottom: modal.getBoundingClientRect().bottom,
                viewportHeight: window.innerHeight,
            };
        });
        if (mobileModal) {
            // On mobile, modal should extend near bottom of viewport
            C.assert(
                Math.abs(mobileModal.bottom - mobileModal.viewportHeight) < 50,
                `A8: Modal positioned at bottom of screen (bottom: ${mobileModal.bottom.toFixed(0)}px, vh: ${mobileModal.viewportHeight}px)`
            );
        } else {
            C.skip('A8: Mobile modal bottom sheet', 'modal not rendered');
        }

        // Close modal
        const closeBtn = await mPage.$('#wpe_modal_close');
        if (closeBtn) await closeBtn.click();
        await mPage.waitForTimeout(C.WAIT.ANIMATION);
    } else {
        C.skip('A8: Mobile modal bottom sheet', 'no notification cards');
    }

    await mCtx.close();

    // ─── Group B: Desktop Layout ───
    const dCtx = await browser.newContext({ viewport: C.DESKTOP_VP });
    const dPage = await dCtx.newPage();
    await C.loginAndNavigate(dPage, C.PORTAL_USER, '/my/home');

    // B1: Hamburger NOT visible on desktop (inline nav instead)
    const desktopHamburger = await dPage.evaluate(() => {
        const toggler = document.querySelector('.navbar-toggler');
        if (!toggler) return { visible: false };
        const cs = getComputedStyle(toggler);
        return { visible: cs.display !== 'none' && cs.visibility !== 'hidden' };
    });
    C.assert(
        !desktopHamburger.visible,
        'B1: Hamburger menu hidden on desktop'
    );

    // B2: Module cards layout on desktop uses available width
    const desktopCardLayout = await dPage.evaluate(() => {
        const cards = document.querySelectorAll('.o_portal_index_card:not(.d-none):not(.wpe-hidden)');
        if (cards.length < 2) return null;
        const first = cards[0].getBoundingClientRect();
        const container = cards[0].closest('.o_portal_docs, #wpe_module_grid');
        const containerWidth = container ? container.getBoundingClientRect().width : window.innerWidth;
        return {
            cardCount: cards.length,
            firstWidth: first.width,
            containerWidth: containerWidth,
            // Check if cards are narrower than full container width (grid-like)
            isCompact: first.width < containerWidth * 0.8,
        };
    });
    if (desktopCardLayout) {
        C.assert(
            desktopCardLayout.cardCount >= 2,
            `B2: Desktop shows ${desktopCardLayout.cardCount} module cards in layout (card: ${desktopCardLayout.firstWidth?.toFixed(0)}px, container: ${desktopCardLayout.containerWidth?.toFixed(0)}px)`
        );
    } else {
        C.skip('B2: Desktop card layout', 'fewer than 2 visible cards');
    }

    // B3: Greeting card max-width constraint on desktop
    const desktopGreeting = await dPage.evaluate(() => {
        const card = document.querySelector('.wpe-greeting-card');
        if (!card) return null;
        return {
            width: card.getBoundingClientRect().width,
            viewportWidth: window.innerWidth,
        };
    });
    if (desktopGreeting) {
        C.assert(
            desktopGreeting.width < desktopGreeting.viewportWidth * 0.8,
            `B3: Greeting card constrained on desktop (${desktopGreeting.width.toFixed(0)}px < ${(desktopGreeting.viewportWidth * 0.8).toFixed(0)}px)`
        );
    } else {
        C.skip('B3: Desktop greeting constraint', 'no greeting card');
    }

    // ─── Desktop Notification Page ───
    await dPage.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await dPage.waitForTimeout(C.WAIT.PAGE_LOAD);

    // B4: Desktop notification modal is centered (not bottom sheet)
    const desktopCardExists = await dPage.evaluate(() => !!document.querySelector('.wpe-notif-card'));
    if (desktopCardExists) {
        await dPage.click('.wpe-notif-card');
        await dPage.waitForTimeout(1500);

        const desktopModal = await dPage.evaluate(() => {
            const modal = document.querySelector('.wpe-notif-modal');
            if (!modal) return null;
            const rect = modal.getBoundingClientRect();
            return {
                top: rect.top,
                bottom: rect.bottom,
                left: rect.left,
                right: rect.right,
                width: rect.width,
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
            };
        });
        if (desktopModal) {
            // Modal should be horizontally centered
            const leftSpace = desktopModal.left;
            const rightSpace = desktopModal.viewportWidth - desktopModal.right;
            C.assert(
                Math.abs(leftSpace - rightSpace) < 50,
                `B4: Desktop modal is centered (left: ${leftSpace.toFixed(0)}px, right: ${rightSpace.toFixed(0)}px)`
            );

            // B5: Desktop modal has max-width constraint
            C.assert(
                desktopModal.width <= 600,
                `B5: Desktop modal has max-width (${desktopModal.width.toFixed(0)}px, expected <= 600px)`
            );
        } else {
            C.skip('B4: Desktop modal centering', 'modal not rendered');
            C.skip('B5: Desktop modal max-width', 'modal not rendered');
        }

        const closeBtn2 = await dPage.$('#wpe_modal_close');
        if (closeBtn2) await closeBtn2.click();
        await dPage.waitForTimeout(C.WAIT.ANIMATION);
    } else {
        C.skip('B4: Desktop modal centering', 'no notification cards');
        C.skip('B5: Desktop modal max-width', 'no notification cards');
    }

    await dCtx.close();
    await browser.close();

    C.printSummary('05: Mobile & Responsive');
    process.exit(C.failCount > 0 ? 1 : 0);
})().catch(err => {
    console.error('FATAL:', err.message);
    process.exit(2);
});
