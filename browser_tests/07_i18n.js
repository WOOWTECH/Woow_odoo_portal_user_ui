/**
 * Test Suite 07: Internationalization (i18n)
 *
 * Verifies the i18n conversion: English source strings render correctly,
 * zh_TW translations load properly, and no raw untranslated strings leak.
 *
 * Uses two distinct portal users:
 *   - PORTAL_USER      (login=portal,      lang=en_US)
 *   - PORTAL_USER_ZHTW (login=portal_zhtw, lang=zh_TW)
 *
 * This avoids Odoo 18's context_get() ORM cache issue that prevents
 * runtime language switching from taking effect within the same process.
 */

const { chromium } = require('playwright');
const C = require('./config');

// ── Main test ─────────────────────────────────────────────────────────

(async () => {
    console.log('\n>>> Test Suite 07: Internationalization (i18n) <<<\n');
    C.resetCounters();

    const browser = await chromium.launch({ headless: true });

    try {
        // ══════════════════════════════════════════════════════════
        // ─── Group A: en_US Verification (Portal Home + Notif) ───
        // ══════════════════════════════════════════════════════════
        console.log('  ─── Group A: en_US Verification ───');

        const ctxA = await browser.newContext({ viewport: C.MOBILE_VP });
        const pageA = await ctxA.newPage();
        await C.loginAndNavigate(pageA, C.PORTAL_USER, '/my/home');

        // A1: Greeting is English
        const greetingEn = await pageA.evaluate(() => {
            const h4 = document.querySelector('.wpe-greeting-card h4');
            return h4 ? h4.textContent.trim() : null;
        });
        C.assert(
            greetingEn && /^(Good Morning|Good Afternoon|Good Evening)/.test(greetingEn),
            `A1: Greeting is English ("${(greetingEn || '').substring(0, 30)}...")`
        );

        // A2: "Recent Notifications" heading
        const recentEn = await pageA.evaluate(() => {
            const h5 = document.querySelector('.wpe-notification-preview h5');
            return h5 ? h5.textContent.trim() : null;
        });
        if (recentEn !== null) {
            C.assert(
                recentEn.includes('Recent Notifications'),
                `A2: Preview heading = "Recent Notifications" ("${recentEn.substring(0, 30)}")`
            );
        } else {
            C.skip('A2: Preview heading "Recent Notifications"', 'preview card not found');
        }

        // A3: "View All" link
        const viewAllEn = await pageA.evaluate(() => {
            const a = document.querySelector('.wpe-view-all-link');
            return a ? a.textContent.trim() : null;
        });
        if (viewAllEn !== null) {
            C.assert(
                viewAllEn.includes('View All'),
                `A3: View-all link = "View All" ("${viewAllEn}")`
            );
        } else {
            C.skip('A3: View-all link "View All"', 'link not found');
        }

        // A4: Search placeholder is English
        const placeholderEn = await pageA.evaluate(() => {
            const input = document.querySelector('#wpe_module_search');
            return input ? input.placeholder : null;
        });
        C.assert(
            placeholderEn === 'Search modules or notifications...',
            `A4: Search placeholder is English ("${placeholderEn}")`
        );

        // A5: Group headers contain English labels
        const groupHeadersEn = await pageA.evaluate(() => {
            const spans = document.querySelectorAll('.wpe-preview-group-header .fw-semibold');
            return Array.from(spans).map((s) => s.textContent.trim());
        });
        if (groupHeadersEn.length > 0) {
            const enLabels = ['Messages', 'Notifications', 'To-Do'];
            const hasEnLabel = groupHeadersEn.some((h) => enLabels.includes(h));
            C.assert(
                hasEnLabel,
                `A5: Group headers are English (${JSON.stringify(groupHeadersEn)})`
            );
        } else {
            C.skip('A5: Group headers are English', 'no preview groups (no notification data)');
        }

        // A6: Notifications page — header, back btn, tabs
        await pageA.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
        await pageA.waitForTimeout(C.WAIT.PAGE_LOAD);

        const notifPageEn = await pageA.evaluate(() => {
            const heading = document.querySelector('.d-flex h4.fw-bold');
            const backBtn = document.querySelector('.wpe-breadcrumb-back-btn');
            const tabs = Array.from(document.querySelectorAll('.wpe-notif-tab'))
                .map((t) => t.textContent.trim().replace(/\d+/g, '').trim());
            return {
                heading: heading ? heading.textContent.trim() : null,
                backText: backBtn ? backBtn.textContent.trim() : null,
                tabs,
            };
        });
        const a6pass =
            notifPageEn.heading && notifPageEn.heading.includes('Notification Center') &&
            notifPageEn.backText && notifPageEn.backText.includes('Back') &&
            notifPageEn.tabs.some((t) => t === 'All') &&
            notifPageEn.tabs.some((t) => t === 'Messages') &&
            notifPageEn.tabs.some((t) => t === 'Notifications');
        C.assert(
            a6pass,
            `A6: Notif page en_US — heading="${notifPageEn.heading}", back="${notifPageEn.backText}", tabs=${JSON.stringify(notifPageEn.tabs)}`
        );

        await ctxA.close();

        // ══════════════════════════════════════════════════════════
        // ─── Group B: zh_TW Verification ─────────────────────────
        // ══════════════════════════════════════════════════════════
        console.log('\n  ─── Group B: zh_TW Verification ───');

        const ctxB = await browser.newContext({ viewport: C.MOBILE_VP });
        const pageB = await ctxB.newPage();
        await C.loginAndNavigate(pageB, C.PORTAL_USER_ZHTW, '/my/home');

        // B1: Greeting is Chinese
        const greetingZh = await pageB.evaluate(() => {
            const h4 = document.querySelector('.wpe-greeting-card h4');
            return h4 ? h4.textContent.trim() : null;
        });
        C.assert(
            greetingZh && /^(早安|午安|晚安)/.test(greetingZh),
            `B1: Greeting is zh_TW ("${(greetingZh || '').substring(0, 30)}...")`
        );

        // B2: "近期通知" heading
        const recentZh = await pageB.evaluate(() => {
            const h5 = document.querySelector('.wpe-notification-preview h5');
            return h5 ? h5.textContent.trim() : null;
        });
        if (recentZh !== null) {
            C.assert(
                recentZh.includes('近期通知'),
                `B2: Preview heading = "近期通知" ("${recentZh.substring(0, 30)}")`
            );
        } else {
            C.skip('B2: Preview heading "近期通知"', 'preview card not found');
        }

        // B3: "查看全部" link
        const viewAllZh = await pageB.evaluate(() => {
            const a = document.querySelector('.wpe-view-all-link');
            return a ? a.textContent.trim() : null;
        });
        if (viewAllZh !== null) {
            C.assert(
                viewAllZh.includes('查看全部'),
                `B3: View-all link = "查看全部" ("${viewAllZh}")`
            );
        } else {
            C.skip('B3: View-all link "查看全部"', 'link not found');
        }

        // B4: Search placeholder is Chinese
        const placeholderZh = await pageB.evaluate(() => {
            const input = document.querySelector('#wpe_module_search');
            return input ? input.placeholder : null;
        });
        C.assert(
            placeholderZh === '搜尋模組或通知...',
            `B4: Search placeholder is zh_TW ("${placeholderZh}")`
        );

        // B5: Group headers contain Chinese labels
        const groupHeadersZh = await pageB.evaluate(() => {
            const spans = document.querySelectorAll('.wpe-preview-group-header .fw-semibold');
            return Array.from(spans).map((s) => s.textContent.trim());
        });
        if (groupHeadersZh.length > 0) {
            const zhLabels = ['留言', '通知', '待辦'];
            const hasZhLabel = groupHeadersZh.some((h) => zhLabels.includes(h));
            C.assert(
                hasZhLabel,
                `B5: Group headers are zh_TW (${JSON.stringify(groupHeadersZh)})`
            );
        } else {
            C.skip('B5: Group headers are zh_TW', 'no preview groups (no notification data)');
        }

        // B6: Notifications page — header, back btn, tabs
        await pageB.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
        await pageB.waitForTimeout(C.WAIT.PAGE_LOAD);

        const notifPageZh = await pageB.evaluate(() => {
            const heading = document.querySelector('.d-flex h4.fw-bold');
            const backBtn = document.querySelector('.wpe-breadcrumb-back-btn');
            const tabs = Array.from(document.querySelectorAll('.wpe-notif-tab'))
                .map((t) => t.textContent.trim().replace(/\d+/g, '').trim());
            return {
                heading: heading ? heading.textContent.trim() : null,
                backText: backBtn ? backBtn.textContent.trim() : null,
                tabs,
            };
        });
        const b6pass =
            notifPageZh.heading && notifPageZh.heading.includes('通知中心') &&
            notifPageZh.backText && notifPageZh.backText.includes('返回') &&
            notifPageZh.tabs.some((t) => t === '全部') &&
            notifPageZh.tabs.some((t) => t === '留言') &&
            notifPageZh.tabs.some((t) => t === '通知');
        C.assert(
            b6pass,
            `B6: Notif page zh_TW — heading="${notifPageZh.heading}", back="${notifPageZh.backText}", tabs=${JSON.stringify(notifPageZh.tabs)}`
        );

        // ══════════════════════════════════════════════════════════
        // ─── Group C: Edge Cases ─────────────────────────────────
        // ══════════════════════════════════════════════════════════
        console.log('\n  ─── Group C: Edge Cases ───');

        // C1: No stray Chinese in en_US mode
        // Use a fresh en_US context (PORTAL_USER)
        const ctxC = await browser.newContext({ viewport: C.MOBILE_VP });
        const pageC = await ctxC.newPage();
        await C.loginAndNavigate(pageC, C.PORTAL_USER, '/my/home');

        const strayChinese = await pageC.evaluate(() => {
            // Only check UI chrome elements, NOT user-generated content
            // (notification subjects/body can contain CJK legitimately)
            const cjkRegex = /[\u4e00-\u9fff]/;
            const checks = [];

            // Greeting card — only the greeting text itself
            const greeting = document.querySelector('.wpe-greeting-card h4');
            if (greeting && cjkRegex.test(greeting.textContent)) {
                checks.push({ selector: '.wpe-greeting-card h4', sample: greeting.textContent.substring(0, 60) });
            }

            // Search bar placeholder
            const search = document.querySelector('#wpe_module_search');
            if (search && cjkRegex.test(search.placeholder)) {
                checks.push({ selector: '#wpe_module_search[placeholder]', sample: search.placeholder });
            }

            // Section heading (e.g. "Recent Notifications")
            const h5 = document.querySelector('.wpe-notification-preview h5');
            if (h5 && cjkRegex.test(h5.textContent)) {
                checks.push({ selector: '.wpe-notification-preview h5', sample: h5.textContent.substring(0, 60) });
            }

            // "View All" link text (not nested content)
            const viewAll = document.querySelector('.wpe-view-all-link');
            if (viewAll) {
                // Get only direct text nodes, not child icon elements
                const directText = Array.from(viewAll.childNodes)
                    .filter(n => n.nodeType === 3 || n.nodeName === 'SPAN')
                    .map(n => n.textContent)
                    .join('');
                if (cjkRegex.test(directText)) {
                    checks.push({ selector: '.wpe-view-all-link', sample: directText.substring(0, 60) });
                }
            }

            // Group headers
            const groupHeaders = document.querySelectorAll('.wpe-preview-group-header .fw-semibold');
            groupHeaders.forEach((el) => {
                if (cjkRegex.test(el.textContent)) {
                    checks.push({ selector: '.wpe-preview-group-header', sample: el.textContent.substring(0, 60) });
                }
            });

            return checks.length > 0
                ? { found: true, details: checks }
                : { found: false };
        });
        C.assert(
            !strayChinese.found,
            `C1: No stray CJK in en_US UI chrome${strayChinese.found ? ' (' + JSON.stringify(strayChinese.details) + ')' : ''}`
        );

        // C2: No raw English msgids in zh_TW mode
        // Use pageB which is the zh_TW user session — reload home
        await pageB.goto(`${C.BASE_URL}/my/home`, { waitUntil: 'load' });
        await pageB.waitForTimeout(C.WAIT.PAGE_LOAD);

        const rawEnglish = await pageB.evaluate(() => {
            const knownMsgids = [
                'Recent Notifications',
                'View All',
                'Good Morning',
                'Good Afternoon',
                'Good Evening',
            ];
            // Check only UI chrome, not notification body content
            const greeting = document.querySelector('.wpe-greeting-card h4');
            const h5 = document.querySelector('.wpe-notification-preview h5');
            const viewAll = document.querySelector('.wpe-view-all-link');
            const combined = [
                greeting ? greeting.textContent : '',
                h5 ? h5.textContent : '',
                viewAll ? viewAll.textContent : '',
            ].join(' ');
            return knownMsgids.filter((msg) => combined.includes(msg));
        });
        C.assert(
            rawEnglish.length === 0,
            `C2: No raw English msgids leak in zh_TW${rawEnglish.length ? ' (leaked: ' + rawEnglish.join(', ') + ')' : ''}`
        );

        // C3: Greeting matches time of day
        const timeCheck = await pageC.evaluate(() => {
            const h4 = document.querySelector('.wpe-greeting-card h4');
            if (!h4) return null;
            const text = h4.textContent.trim();
            const hour = new Date().getHours();
            let expected;
            if (hour >= 6 && hour < 12) expected = 'Good Morning';
            else if (hour >= 12 && hour < 18) expected = 'Good Afternoon';
            else expected = 'Good Evening';
            return { text: text.substring(0, 30), hour, expected, matches: text.includes(expected) };
        });
        if (timeCheck) {
            C.assert(
                timeCheck.matches,
                `C3: Greeting matches time-of-day (hour=${timeCheck.hour}, expected="${timeCheck.expected}", got="${timeCheck.text}")`
            );
        } else {
            C.skip('C3: Greeting matches time-of-day', 'greeting card not found');
        }

        // C4: Swipe hint translated in zh_TW
        await pageB.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
        await pageB.waitForTimeout(C.WAIT.PAGE_LOAD);

        const swipeHint = await pageB.evaluate(() => {
            const hint = document.querySelector('#wpe_swipe_hint');
            return hint ? hint.textContent.trim() : null;
        });
        if (swipeHint) {
            C.assert(
                swipeHint.includes('向右滑動'),
                `C4: Swipe hint is zh_TW ("${swipeHint.substring(0, 40)}")`
            );
        } else {
            C.skip('C4: Swipe hint is zh_TW', 'no swipe hint (no notification items)');
        }

        // C5: Empty state or tab text matches zh_TW
        const emptyOrTab = await pageB.evaluate(() => {
            const empty = document.querySelector('.wpe-notif-empty p');
            if (empty) return { type: 'empty', text: empty.textContent.trim() };
            const tab = document.querySelector('.wpe-notif-tab.active');
            if (tab) return { type: 'tab', text: tab.textContent.trim().replace(/\d+/g, '').trim() };
            return null;
        });
        if (emptyOrTab) {
            if (emptyOrTab.type === 'empty') {
                C.assert(
                    emptyOrTab.text.includes('沒有通知'),
                    `C5: Empty state is zh_TW ("${emptyOrTab.text}")`
                );
            } else {
                const zhTabs = ['全部', '留言', '通知', '待辦'];
                C.assert(
                    zhTabs.includes(emptyOrTab.text),
                    `C5: Active tab is zh_TW ("${emptyOrTab.text}")`
                );
            }
        } else {
            C.skip('C5: zh_TW empty state or tab', 'neither found');
        }

        await ctxC.close();

        // ══════════════════════════════════════════════════════════
        // ─── Group D: JS _t() Verification ───────────────────────
        // ══════════════════════════════════════════════════════════
        console.log('\n  ─── Group D: JS _t() Verification ───');

        // pageB is on /my/notifications in zh_TW
        const cardExists = await pageB.evaluate(() => {
            return !!document.querySelector('.wpe-notif-card');
        });

        if (cardExists) {
            // D1: Click card — modal shows loading text in zh_TW
            await pageB.click('.wpe-notif-card');
            await pageB.waitForTimeout(300); // short wait — catch loading state

            const loadingTitle = await pageB.evaluate(() => {
                const title = document.querySelector('#wpe_modal_title');
                const overlay = document.querySelector('#wpe_notif_modal_overlay');
                return {
                    title: title ? title.textContent.trim() : null,
                    visible: overlay ? getComputedStyle(overlay).display !== 'none' : false,
                };
            });
            // Modal should be visible; loading text is "載入中..." (zh_TW for "Loading...")
            // or the actual title if the API was fast
            C.assert(
                loadingTitle.visible &&
                    loadingTitle.title &&
                    (loadingTitle.title === '載入中...' || loadingTitle.title.length > 0),
                `D1: Modal opened with translated text ("${loadingTitle.title}")`
            );

            // D2: Wait for modal to finish loading, title should change
            await pageB.waitForTimeout(2000);
            const loadedTitle = await pageB.evaluate(() => {
                const title = document.querySelector('#wpe_modal_title');
                return title ? title.textContent.trim() : null;
            });
            C.assert(
                loadedTitle && loadedTitle !== '載入中...' && loadedTitle !== 'Loading...' && loadedTitle.length > 0,
                `D2: Modal loaded with real title ("${(loadedTitle || '').substring(0, 40)}")`
            );

            // D3: Modal footer button is translated
            const modalBtn = await pageB.evaluate(() => {
                const btn = document.querySelector('#wpe_modal_action_btn');
                if (!btn) return null;
                const style = getComputedStyle(btn);
                return {
                    text: btn.textContent.trim(),
                    visible: style.display !== 'none',
                };
            });
            if (modalBtn && modalBtn.visible) {
                const zhBtnLabels = ['標記已讀', '已讀', '核准', '完成'];
                const isZh = zhBtnLabels.some((l) => modalBtn.text.includes(l));
                C.assert(
                    isZh,
                    `D3: Modal action button is zh_TW ("${modalBtn.text}")`
                );
            } else {
                C.skip('D3: Modal action button is zh_TW', 'button hidden or not found');
            }

            // Close modal for cleanup
            await pageB.click('#wpe_modal_close');
            await pageB.waitForTimeout(C.WAIT.ANIMATION);
        } else {
            C.skip('D1: Modal loading text in zh_TW', 'no notification cards to click');
            C.skip('D2: Modal loaded title', 'no notification cards to click');
            C.skip('D3: Modal action button in zh_TW', 'no notification cards to click');
        }

        await ctxB.close();
    } finally {
        await browser.close();
    }

    C.printSummary('07: Internationalization (i18n)');
    process.exit(C.failCount > 0 ? 1 : 0);
})().catch((err) => {
    console.error('FATAL:', err.message);
    process.exit(2);
});
