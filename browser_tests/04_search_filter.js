/**
 * Test Suite 04: Search & Filtering
 *
 * Tests:
 * - Module search bar on portal home
 * - Module card filtering by keyword
 * - Category visibility when all children hidden
 * - Notification preview filtering
 * - Notification list search/filter/sort/group
 * - Case-insensitive matching
 * - Empty search restores all items
 */

const { chromium } = require('playwright');
const C = require('./config');

(async () => {
    console.log('\n>>> Test Suite 04: Search & Filtering <<<\n');
    C.resetCounters();

    const browser = await chromium.launch({ headless: true });
    const ctx = await browser.newContext({ viewport: C.MOBILE_VP });
    const page = await ctx.newPage();

    // ─── Group A: Module Search on Home ───
    await C.loginAndNavigate(page, C.PORTAL_USER, '/my/home');
    // Wait for spinner to clear and cards to be ready
    await page.waitForTimeout(2000);

    // A1: Search input exists
    const searchInput = await page.evaluate(() => {
        const input = document.querySelector('#wpe_module_search');
        if (!input) return null;
        return { placeholder: input.placeholder, type: input.type };
    });
    C.assert(
        searchInput !== null,
        `A1: Module search input exists (placeholder: "${searchInput?.placeholder}")`
    );

    // A2: Count visible module cards before search
    const initialCardCount = await page.evaluate(() => {
        const cards = document.querySelectorAll('.o_portal_index_card');
        let visible = 0;
        cards.forEach(c => {
            if (!c.classList.contains('wpe-hidden') && !c.classList.contains('d-none')) visible++;
        });
        return visible;
    });
    C.assert(
        initialCardCount >= 0,
        `A2: Initial visible module cards: ${initialCardCount}`
    );

    if (searchInput && initialCardCount > 0) {
        // A3: Type a search query that should filter results
        // JS uses 'keyup' event, so we need to type character by character
        await page.click('#wpe_module_search');
        await page.keyboard.type('zzz_nonexistent', { delay: 30 });
        await page.waitForTimeout(C.WAIT.DEBOUNCE);

        const filteredCount = await page.evaluate(() => {
            const cards = document.querySelectorAll('.o_portal_index_card');
            let visible = 0;
            cards.forEach(c => {
                if (!c.classList.contains('wpe-hidden') && !c.classList.contains('d-none')) visible++;
            });
            return visible;
        });
        C.assert(
            filteredCount < initialCardCount,
            `A3: Search filter reduces visible cards (${initialCardCount} → ${filteredCount})`
        );

        // A4: Clear search restores cards
        await page.fill('#wpe_module_search', '');
        await page.evaluate(() => {
            const input = document.querySelector('#wpe_module_search');
            if (input) input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
        });
        await page.waitForTimeout(C.WAIT.DEBOUNCE);

        const restoredCount = await page.evaluate(() => {
            const cards = document.querySelectorAll('.o_portal_index_card');
            let visible = 0;
            cards.forEach(c => {
                if (!c.classList.contains('wpe-hidden') && !c.classList.contains('d-none')) visible++;
            });
            return visible;
        });
        C.assert(
            restoredCount >= initialCardCount,
            `A4: Clearing search restores cards (${restoredCount} visible)`
        );

        // A5: Case-insensitive search (type uppercase of known module)
        // First find a card name to search for
        const cardName = await page.evaluate(() => {
            const title = document.querySelector('.o_portal_index_card:not(.d-none) .card-title');
            return title ? title.textContent.trim() : null;
        });
        if (cardName) {
            await page.fill('#wpe_module_search', '');
            await page.click('#wpe_module_search');
            await page.keyboard.type(cardName.toUpperCase().substring(0, 3), { delay: 30 });
            await page.waitForTimeout(C.WAIT.DEBOUNCE);

            const upperSearchCount = await page.evaluate(() => {
                const cards = document.querySelectorAll('.o_portal_index_card');
                let visible = 0;
                cards.forEach(c => {
                    if (!c.classList.contains('wpe-hidden') && !c.classList.contains('d-none')) visible++;
                });
                return visible;
            });
            C.assert(
                upperSearchCount > 0,
                `A5: Case-insensitive search works (searched "${cardName.toUpperCase().substring(0, 3)}", found ${upperSearchCount})`
            );
            await page.fill('#wpe_module_search', '');
            await page.waitForTimeout(C.WAIT.DEBOUNCE);
        } else {
            C.skip('A5: Case-insensitive search', 'no card title to test with');
        }

        // A6: Category sections hide when all children are filtered
        const hasCategories = await page.evaluate(() => {
            return document.querySelectorAll('.o_portal_category').length > 0;
        });
        if (hasCategories) {
            await page.fill('#wpe_module_search', '');
            await page.click('#wpe_module_search');
            await page.keyboard.type('zzz_impossible_query', { delay: 20 });
            await page.waitForTimeout(C.WAIT.DEBOUNCE);

            const hiddenCategories = await page.evaluate(() => {
                const cats = document.querySelectorAll('.o_portal_category');
                let allHidden = true;
                cats.forEach(c => {
                    if (!c.classList.contains('wpe-hidden') && !c.classList.contains('d-none')) {
                        allHidden = false;
                    }
                });
                return allHidden;
            });
            C.assert(
                hiddenCategories,
                'A6: Categories hide when all children are filtered out'
            );
            await page.fill('#wpe_module_search', '');
            await page.waitForTimeout(C.WAIT.DEBOUNCE);
        } else {
            C.skip('A6: Category section hiding', 'no categories found');
        }
    }

    // ─── Group B: Notification List Filters ───
    await page.goto(`${C.BASE_URL}/my/notifications`, { waitUntil: 'load' });
    await page.waitForTimeout(C.WAIT.PAGE_LOAD);

    const notifCardCount = await page.evaluate(() => document.querySelectorAll('.wpe-notif-card-wrapper').length);

    // B1: Filter toolbar toggle
    const filterToggle = await page.evaluate(() => !!document.querySelector('#wpe_notif_searchbar_toggle'));
    C.assert(filterToggle, 'B1: Filter toolbar toggle button exists');

    if (filterToggle && notifCardCount > 0) {
        // B2: Toggle opens filter panel
        await page.click('#wpe_notif_searchbar_toggle');
        await page.waitForTimeout(C.WAIT.SHORT);

        const panelVisible = await page.evaluate(() => {
            const panel = document.querySelector('#wpe_notif_searchbar');
            return panel ? !panel.classList.contains('d-none') : false;
        });
        C.assert(panelVisible, 'B2: Filter panel opens after toggle click');

        // B3: Sort buttons exist
        const sortBtns = await page.evaluate(() => {
            const btns = document.querySelectorAll('.wpe-notif-sort-btn');
            return Array.from(btns).map(b => ({
                text: b.textContent.trim(),
                sort: b.getAttribute('data-sort'),
                active: b.classList.contains('active'),
            }));
        });
        C.assert(
            sortBtns.length >= 2,
            `B3: Sort buttons exist (${sortBtns.map(b => b.sort).join(', ')})`
        );

        // B4: Filter buttons exist
        const filterBtns = await page.evaluate(() => {
            const btns = document.querySelectorAll('.wpe-notif-filter-btn');
            return Array.from(btns).map(b => ({
                text: b.textContent.trim(),
                filter: b.getAttribute('data-filter'),
                active: b.classList.contains('active'),
            }));
        });
        C.assert(
            filterBtns.length >= 3,
            `B4: Filter buttons exist (${filterBtns.map(b => b.filter).join(', ')})`
        );

        // B5: Group buttons exist
        const groupBtns = await page.evaluate(() => {
            const btns = document.querySelectorAll('.wpe-notif-group-btn');
            return Array.from(btns).map(b => ({
                text: b.textContent.trim(),
                group: b.getAttribute('data-group'),
                active: b.classList.contains('active'),
            }));
        });
        C.assert(
            groupBtns.length >= 2,
            `B5: Group buttons exist (${groupBtns.map(b => b.group).join(', ')})`
        );

        // B6: Filter "unread" — should hide read cards
        const unreadFilterBtn = await page.$('.wpe-notif-filter-btn[data-filter="unread"]');
        if (unreadFilterBtn) {
            await unreadFilterBtn.click();
            await page.waitForTimeout(C.WAIT.SHORT);

            const readHidden = await page.evaluate(() => {
                const readCards = document.querySelectorAll('.wpe-notif-read');
                let hidden = 0;
                readCards.forEach(c => {
                    const wrapper = c.closest('.wpe-notif-card-wrapper');
                    if (wrapper && wrapper.classList.contains('wpe-filter-hidden')) hidden++;
                });
                return { total: readCards.length, hidden };
            });
            C.assert(
                readHidden.total === 0 || readHidden.hidden === readHidden.total,
                `B6: "Unread" filter hides read cards (${readHidden.hidden}/${readHidden.total} hidden)`
            );

            // Reset to "all"
            const allBtn = await page.$('.wpe-notif-filter-btn[data-filter="all"]');
            if (allBtn) await allBtn.click();
            await page.waitForTimeout(C.WAIT.SHORT);
        } else {
            C.skip('B6: Unread filter', 'no unread filter button');
        }

        // B7: Group by type — should insert group headers
        const typeGroupBtn = await page.$('.wpe-notif-group-btn[data-group="type"]');
        if (typeGroupBtn) {
            await typeGroupBtn.click();
            await page.waitForTimeout(C.WAIT.SHORT);

            const groupHeaders = await page.evaluate(() => {
                return document.querySelectorAll('.wpe-notif-group-header').length;
            });
            C.assert(
                groupHeaders > 0,
                `B7: Group by type inserts group headers (${groupHeaders} headers)`
            );

            // Reset to "none"
            const noneBtn = await page.$('.wpe-notif-group-btn[data-group="none"]');
            if (noneBtn) await noneBtn.click();
            await page.waitForTimeout(C.WAIT.SHORT);
        } else {
            C.skip('B7: Group by type', 'no group type button');
        }

        // B8: Text search in notifications
        const searchInput2 = await page.$('#wpe_notif_search_input');
        if (searchInput2) {
            await page.click('#wpe_notif_search_input');
            await page.keyboard.type('zzz_impossible', { delay: 30 });
            await page.waitForTimeout(C.WAIT.DEBOUNCE + 300);

            const hiddenBySearch = await page.evaluate(() => {
                const wrappers = document.querySelectorAll('.wpe-notif-card-wrapper');
                let hidden = 0;
                wrappers.forEach(w => {
                    if (w.classList.contains('wpe-filter-hidden')) hidden++;
                });
                return { total: wrappers.length, hidden };
            });
            C.assert(
                hiddenBySearch.hidden === hiddenBySearch.total,
                `B8: Text search filters notifications (${hiddenBySearch.hidden}/${hiddenBySearch.total} hidden)`
            );

            // Clear
            await page.fill('#wpe_notif_search_input', '');
            await page.evaluate(() => {
                const input = document.querySelector('#wpe_notif_search_input');
                if (input) input.dispatchEvent(new Event('input', { bubbles: true }));
            });
            await page.waitForTimeout(C.WAIT.DEBOUNCE);
        } else {
            C.skip('B8: Text search', 'no search input found');
        }

        // Close filter panel
        await page.click('#wpe_notif_searchbar_toggle');
        await page.waitForTimeout(C.WAIT.SHORT);
    } else if (notifCardCount === 0) {
        C.skip('B2-B8: Notification filters', 'no notification cards to filter');
    }

    await ctx.close();
    await browser.close();

    C.printSummary('04: Search & Filtering');
    process.exit(C.failCount > 0 ? 1 : 0);
})().catch(err => {
    console.error('FATAL:', err.message);
    process.exit(2);
});
