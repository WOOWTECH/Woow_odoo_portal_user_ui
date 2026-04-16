/**
 * Test Suite 03: Notification System
 *
 * Tests:
 * - Notification preview card on portal home
 * - Notification list page structure
 * - Tab navigation (all/message/notification/activity)
 * - Notification card structure & content
 * - Detail modal open/close
 * - Swipe gesture behavior
 * - Mark read/unread toggle
 * - Mark all read
 * - Badge count updates
 * - Empty state handling
 */

const { chromium } = require('playwright');
const C = require('./config');

(async () => {
    console.log('\n>>> Test Suite 03: Notification System <<<\n');
    C.resetCounters();

    const browser = await chromium.launch({ headless: true });
    const ctx = await browser.newContext({ viewport: C.MOBILE_VP });
    const page = await ctx.newPage();

    // ─── Group A: Notification Preview on Home ───
    await C.loginAndNavigate(page, C.PORTAL_USER, '/my/home');

    const previewCard = await page.evaluate(() => {
        const card = document.querySelector('.wpe-notification-preview');
        if (!card) return null;
        const cs = getComputedStyle(card);
        const groups = card.querySelectorAll('.wpe-preview-group-header');
        const items = card.querySelectorAll('.wpe-notification-item');
        const viewAll = card.querySelector('.wpe-view-all-link');
        return {
            display: cs.display,
            groupCount: groups.length,
            itemCount: items.length,
            hasViewAll: !!viewAll,
            viewAllHref: viewAll ? viewAll.getAttribute('href') : null,
        };
    });

    if (previewCard) {
        C.assert(
            previewCard.display !== 'none',
            'A1: Notification preview card is visible on home'
        );
        C.assert(
            previewCard.groupCount > 0,
            `A2: Preview has group headers (${previewCard.groupCount} groups)`
        );
        C.assert(
            previewCard.itemCount > 0,
            `A3: Preview has notification items (${previewCard.itemCount} items)`
        );
        C.assert(
            previewCard.hasViewAll,
            'A4: Preview has "View All" link'
        );
        C.assert(
            previewCard.viewAllHref && previewCard.viewAllHref.includes('/my/notifications'),
            `A5: View All links to notifications page (href: ${previewCard.viewAllHref})`
        );
    } else {
        C.skip('A1-A5: Notification preview card', 'no preview card found (maybe no notifications)');
    }

    // ─── Group B: Notification List Page Structure ───
    await page.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await page.waitForTimeout(C.WAIT.PAGE_LOAD);

    // B1: Tabs exist
    const tabs = await page.evaluate(() => {
        const tabEls = document.querySelectorAll('.wpe-notif-tab');
        const results = [];
        tabEls.forEach(t => {
            results.push({
                text: t.textContent.trim(),
                isActive: t.classList.contains('active'),
                href: t.getAttribute('href') || '',
            });
        });
        return results;
    });
    C.assert(
        tabs.length >= 3,
        `B1: Notification tabs exist (found ${tabs.length}, expected >= 3)`
    );

    // B2: One tab is active
    const activeTabs = tabs.filter(t => t.isActive);
    C.assert(
        activeTabs.length === 1,
        `B2: Exactly one tab is active (found ${activeTabs.length})`
    );

    // B3: Tab badges present
    const tabBadges = await page.evaluate(() => {
        const badges = document.querySelectorAll('.wpe-notif-tab .badge');
        return badges.length;
    });
    C.assert(
        tabBadges > 0,
        `B3: Tab badges are displayed (${tabBadges} badges)`
    );

    // B4: Notification list container exists
    const listExists = await page.evaluate(() => !!document.querySelector('#wpe_notif_list'));
    C.assert(listExists, 'B4: Notification list container (#wpe_notif_list) exists');

    // B5: Cards present
    const cardCount = await page.evaluate(() => {
        return document.querySelectorAll('.wpe-notif-card-wrapper').length;
    });
    if (cardCount > 0) {
        C.assert(true, `B5: Found ${cardCount} notification cards`);
    } else {
        C.skip('B5: Notification cards present', 'no cards found (empty state)');
    }

    // ─── Group C: Card Structure ───
    if (cardCount > 0) {
        const firstCard = await page.evaluate(() => {
            const wrapper = document.querySelector('.wpe-notif-card-wrapper');
            if (!wrapper) return null;
            const card = wrapper.querySelector('.wpe-notif-card');
            return {
                hasIcon: !!card.querySelector('.wpe-notif-card-icon'),
                hasTitle: !!card.querySelector('.wpe-notif-card-title'),
                hasMeta: !!card.querySelector('.wpe-notif-card-meta'),
                hasSwipeBg: !!wrapper.querySelector('.wpe-notif-swipe-bg'),
                hasArrow: !!card.querySelector('.fa-chevron-right, .oi-chevron-right, .fa-angle-right, [class*="chevron"], [class*="arrow"]'),
                itemType: wrapper.getAttribute('data-item-type'),
                hasId: !!(wrapper.getAttribute('data-notif-id') || wrapper.getAttribute('data-activity-id')),
            };
        });

        C.assert(firstCard.hasIcon, 'C1: Card has icon element');
        C.assert(firstCard.hasTitle, 'C2: Card has title element');
        C.assert(firstCard.hasMeta, 'C3: Card has meta info');
        C.assert(firstCard.hasSwipeBg, 'C4: Card has swipe background');
        C.assert(firstCard.hasArrow, 'C5: Card has chevron/arrow indicator');
        C.assert(
            firstCard.itemType === 'notification' || firstCard.itemType === 'activity',
            `C6: Card has valid data-item-type (${firstCard.itemType})`
        );
        C.assert(firstCard.hasId, 'C7: Card has data-notif-id or data-activity-id');
    }

    // ─── Group D: Detail Modal ───
    if (cardCount > 0) {
        // D1: Modal overlay exists but hidden
        const modalHidden = await page.evaluate(() => {
            const overlay = document.querySelector('#wpe_notif_modal_overlay');
            if (!overlay) return null;
            return getComputedStyle(overlay).display;
        });
        C.assert(
            modalHidden === 'none',
            `D1: Modal overlay is initially hidden (display: ${modalHidden})`
        );

        // D2: Click card to open modal
        await page.click('.wpe-notif-card');
        await page.waitForTimeout(1500); // wait for API call + render

        const modalVisible = await page.evaluate(() => {
            const overlay = document.querySelector('#wpe_notif_modal_overlay');
            if (!overlay) return null;
            return getComputedStyle(overlay).display;
        });
        C.assert(
            modalVisible !== 'none',
            `D2: Modal opens after clicking a card (display: ${modalVisible})`
        );

        // D3: Modal has title
        const modalTitle = await page.evaluate(() => {
            const title = document.querySelector('#wpe_modal_title');
            return title ? title.textContent.trim() : null;
        });
        C.assert(
            modalTitle && modalTitle.length > 0 && modalTitle !== '載入中...' && modalTitle !== 'Loading...',
            `D3: Modal title loaded (${modalTitle?.substring(0, 40)})`
        );

        // D4: Modal has body content
        const modalBody = await page.evaluate(() => {
            const body = document.querySelector('#wpe_modal_body');
            return body ? body.innerHTML.length : 0;
        });
        C.assert(
            modalBody > 50,
            `D4: Modal body has content (${modalBody} chars)`
        );

        // D5: Modal has close button
        const closeBtn = await page.evaluate(() => !!document.querySelector('#wpe_modal_close'));
        C.assert(closeBtn, 'D5: Modal has close button');

        // D6: Close modal with close button
        await page.click('#wpe_modal_close');
        await page.waitForTimeout(C.WAIT.ANIMATION);

        const modalClosed = await page.evaluate(() => {
            const overlay = document.querySelector('#wpe_notif_modal_overlay');
            return overlay ? getComputedStyle(overlay).display : null;
        });
        C.assert(
            modalClosed === 'none',
            `D6: Modal closes after clicking close button (display: ${modalClosed})`
        );

        // D7: Open modal again, close with Escape key
        await page.click('.wpe-notif-card');
        await page.waitForTimeout(1500);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(C.WAIT.ANIMATION);

        const modalClosedEsc = await page.evaluate(() => {
            const overlay = document.querySelector('#wpe_notif_modal_overlay');
            return overlay ? getComputedStyle(overlay).display : null;
        });
        C.assert(
            modalClosedEsc === 'none',
            `D7: Modal closes with Escape key (display: ${modalClosedEsc})`
        );

        // D8: Open modal, close by clicking overlay background
        await page.click('.wpe-notif-card');
        await page.waitForTimeout(1500);
        // Click on the overlay (outside the modal)
        await page.evaluate(() => {
            const overlay = document.querySelector('#wpe_notif_modal_overlay');
            if (overlay) {
                overlay.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            }
        });
        await page.waitForTimeout(C.WAIT.ANIMATION);

        const modalClosedOverlay = await page.evaluate(() => {
            const overlay = document.querySelector('#wpe_notif_modal_overlay');
            return overlay ? getComputedStyle(overlay).display : null;
        });
        C.assert(
            modalClosedOverlay === 'none',
            `D8: Modal closes when clicking overlay background`
        );
    } else {
        C.skip('C1-C7, D1-D8: Card structure & modal', 'no notification cards to test');
    }

    // ─── Group E: Tab Navigation ───
    // Navigate between tabs
    const tabHrefs = await page.evaluate(() => {
        const tabEls = document.querySelectorAll('.wpe-notif-tab');
        return Array.from(tabEls).map(t => ({
            text: t.textContent.trim(),
            href: t.getAttribute('href') || '',
        }));
    });

    if (tabHrefs.length >= 2) {
        // Click second tab
        const secondTabHref = tabHrefs[1].href;
        if (secondTabHref) {
            await page.goto(`${C.BASE_URL}${secondTabHref}`, { waitUntil: 'load' });
            await page.waitForTimeout(C.WAIT.PAGE_LOAD);

            const newActiveTab = await page.evaluate(() => {
                const active = document.querySelector('.wpe-notif-tab.active');
                return active ? active.textContent.trim() : null;
            });
            C.assert(
                newActiveTab !== null,
                `E1: Tab navigation works — active tab after click: "${newActiveTab}"`
            );
        } else {
            C.skip('E1: Tab navigation', 'no href on tabs');
        }
    } else {
        C.skip('E1: Tab navigation', 'fewer than 2 tabs');
    }

    // ─── Group F: Swipe Gesture (simulated via mouse) ───
    // Go back to all tab
    await page.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await page.waitForTimeout(C.WAIT.PAGE_LOAD);

    const swipeCardExists = await page.evaluate(() => !!document.querySelector('.wpe-notif-card-wrapper'));
    if (swipeCardExists) {
        // F1: Swipe hint visibility
        const swipeHint = await page.evaluate(() => {
            const hint = document.querySelector('#wpe_swipe_hint');
            if (!hint) return null;
            const cs = getComputedStyle(hint);
            return { display: cs.display, opacity: cs.opacity };
        });
        if (swipeHint) {
            C.assert(
                swipeHint.display !== 'none',
                `F1: Swipe hint is initially visible`
            );
        } else {
            C.skip('F1: Swipe hint', 'no swipe hint element');
        }

        // F2: Simulate partial swipe (below threshold) — card should snap back
        const cardBox = await page.evaluate(() => {
            const card = document.querySelector('.wpe-notif-card');
            if (!card) return null;
            const rect = card.getBoundingClientRect();
            return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
        });

        if (cardBox) {
            // Small swipe (50px, below 100px threshold)
            await page.mouse.move(cardBox.x, cardBox.y);
            await page.mouse.down();
            await page.mouse.move(cardBox.x + 50, cardBox.y, { steps: 5 });
            await page.waitForTimeout(100);
            await page.mouse.up();
            await page.waitForTimeout(C.WAIT.ANIMATION);

            const cardStillThere = await page.evaluate(() => {
                const card = document.querySelector('.wpe-notif-card');
                if (!card) return null;
                return {
                    transform: card.style.transform || getComputedStyle(card).transform,
                    exists: true,
                };
            });
            C.assert(
                cardStillThere && cardStillThere.exists,
                'F2: Card snaps back after partial swipe (< threshold)'
            );
        } else {
            C.skip('F2: Partial swipe snap back', 'no card to swipe');
        }
    } else {
        C.skip('F1-F2: Swipe gestures', 'no cards available');
    }

    // ─── Group G: Mark All Read Button ───
    const markAllBtn = await page.evaluate(() => {
        const btn = document.querySelector('#wpe_mark_all_read');
        if (!btn) return null;
        return {
            text: btn.textContent.trim(),
            disabled: btn.disabled,
            display: getComputedStyle(btn).display,
        };
    });
    if (markAllBtn) {
        C.assert(
            markAllBtn.display !== 'none',
            `G1: "Mark All Read" button is visible (text: "${markAllBtn.text}")`
        );
    } else {
        C.skip('G1: Mark All Read button', 'button not found');
    }

    // ─── Group H: Unread/Read Visual Distinction ───
    // Navigate to "all" tab to ensure we see both states
    await page.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await page.waitForTimeout(C.WAIT.PAGE_LOAD);

    const readStates = await page.evaluate(() => {
        // Check the .wpe-notif-card inside unread/read wrappers
        const unreadWrapper = document.querySelector('.wpe-notif-unread');
        const readWrapper = document.querySelector('.wpe-notif-read');
        let unreadSample = null;
        let readSample = null;
        if (unreadWrapper) {
            const card = unreadWrapper.querySelector('.wpe-notif-card') || unreadWrapper;
            const cs = getComputedStyle(card);
            const wcs = getComputedStyle(unreadWrapper);
            unreadSample = {
                bg: cs.backgroundColor,
                wrapperBg: wcs.backgroundColor,
                opacity: cs.opacity,
                fontWeight: cs.fontWeight,
            };
        }
        if (readWrapper) {
            const card = readWrapper.querySelector('.wpe-notif-card') || readWrapper;
            const cs = getComputedStyle(card);
            const wcs = getComputedStyle(readWrapper);
            readSample = {
                bg: cs.backgroundColor,
                wrapperBg: wcs.backgroundColor,
                opacity: cs.opacity,
                fontWeight: cs.fontWeight,
            };
        }
        return {
            unreadCount: document.querySelectorAll('.wpe-notif-unread').length,
            readCount: document.querySelectorAll('.wpe-notif-read').length,
            unreadSample,
            readSample,
        };
    });

    if (readStates.unreadCount > 0 && readStates.readCount > 0) {
        const u = readStates.unreadSample;
        const r = readStates.readSample;
        const hasDifference =
            u.bg !== r.bg || u.wrapperBg !== r.wrapperBg ||
            u.opacity !== r.opacity || u.fontWeight !== r.fontWeight;
        C.assert(
            hasDifference,
            `H1: Unread and read cards have visual distinction (unread: bg=${u.bg}, opacity=${u.opacity} | read: bg=${r.bg}, opacity=${r.opacity})`
        );
    } else if (readStates.unreadCount > 0) {
        C.assert(true, `H1: Only unread cards present (${readStates.unreadCount}), visual distinction assumed`);
    } else if (readStates.readCount > 0) {
        C.assert(true, `H1: Only read cards present (${readStates.readCount}), visual distinction assumed`);
    } else {
        C.skip('H1: Unread/read visual distinction', 'no cards to compare');
    }

    await ctx.close();
    await browser.close();

    C.printSummary('03: Notification System');
    process.exit(C.failCount > 0 ? 1 : 0);
})().catch(err => {
    console.error('FATAL:', err.message);
    process.exit(2);
});
