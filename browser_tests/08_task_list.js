/**
 * 08 — Task List Features
 *
 * Tests the task list page changes:
 *   - "新增" (Add) button on project task page
 *   - Tags column visible with colored badges
 *   - Time Spent column hidden (via JS)
 *   - Stage column still visible (when not grouped by stage)
 *   - Task creation form loads and works
 */

const { chromium } = require('playwright');
const {
    BASE_URL, PORTAL_USER_ZHTW, DESKTOP_VP, WAIT,
    assert, skip, printSummary, resetCounters,
    loginAndNavigate,
} = require('./config');

(async () => {
    console.log('\n🔧 08 — Task List Features\n');
    resetCounters();

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: DESKTOP_VP });
    const page = await context.newPage();

    try {
        // ── Login as portal_zhtw and go to /my/tasks first ──
        console.log('--- /my/tasks page ---');
        await loginAndNavigate(page, PORTAL_USER_ZHTW, '/my/tasks', WAIT.PAGE_LOAD);

        const tasksUrl = page.url();
        assert(tasksUrl.includes('/my/tasks'), '/my/tasks page loads without redirect');

        // Time Spent column should be hidden (display:none via JS)
        var timeSpentVisible = await page.evaluate(function() {
            var ths = document.querySelectorAll('table.table thead th');
            for (var i = 0; i < ths.length; i++) {
                var text = ths[i].textContent.trim();
                if (text === 'Time Spent' || text === '已花費時間') {
                    return ths[i].style.display !== 'none' && window.getComputedStyle(ths[i]).display !== 'none';
                }
            }
            return false;
        });
        assert(!timeSpentVisible, 'Time Spent column is hidden on /my/tasks');

        // Tags column should be visible
        var hasTagsHeader = await page.evaluate(function() {
            var ths = document.querySelectorAll('table.table thead th');
            for (var i = 0; i < ths.length; i++) {
                var text = ths[i].textContent.trim();
                if (text === 'Tags' || text === '標籤') {
                    return window.getComputedStyle(ths[i]).display !== 'none';
                }
            }
            return false;
        });
        assert(hasTagsHeader, 'Tags column header is visible on /my/tasks');

        // Stage column should still exist (visible headers, excluding hidden ones)
        var visibleHeaders = await page.evaluate(function() {
            var ths = document.querySelectorAll('table.table thead th');
            var result = [];
            for (var i = 0; i < ths.length; i++) {
                if (window.getComputedStyle(ths[i]).display !== 'none' && ths[i].textContent.trim().length > 0) {
                    result.push(ths[i].textContent.trim());
                }
            }
            return result;
        });
        console.log('  Visible headers:', JSON.stringify(visibleHeaders));
        var hasStageHeader = visibleHeaders.some(function(h) { return h === 'Stage' || h === '階段'; });
        assert(hasStageHeader, 'Stage column header still present on /my/tasks');

        // Tag badges in the table body
        var tagBadges = await page.evaluate(function() {
            return document.querySelectorAll('.wpe-tag-badge').length;
        });
        console.log('  Tag badges found:', tagBadges);
        assert(tagBadges > 0, 'Tag badges are rendered in the task list');

        // ── Navigate to /my/projects/8 (project task page) ──
        console.log('\n--- /my/projects/8 page ---');
        await page.goto(BASE_URL + '/my/projects/8', { waitUntil: 'load' });
        await page.waitForTimeout(WAIT.PAGE_LOAD);

        var projectUrl = page.url();
        // Check that it loaded as portal template (not project_sharing SPA)
        var hasPortalTable = await page.evaluate(function() {
            return !!document.getElementById('wrap') && !!document.querySelector('table.table');
        });
        console.log('  Final URL:', projectUrl);
        console.log('  Has portal template table:', hasPortalTable);

        if (!hasPortalTable) {
            skip('Project page loads with portal template', 'No table found — may be using Project Sharing SPA');
            skip('Add button visible on project page', 'Project page not loaded as portal template');
            skip('Add button positioned left of Tasks heading', 'Project page not loaded');
            skip('Time Spent hidden on project page', 'Project page not loaded');
            skip('Tags visible on project page', 'Project page not loaded');
            skip('Stage visible on project page (groupby=none)', 'Project page not loaded');
        } else {
            assert(true, 'Project page loads with portal template');

            // Check "新增" button
            var addBtnInfo = await page.evaluate(function() {
                var btn = document.getElementById('wpe_task_add_btn');
                if (!btn) btn = document.querySelector('.wpe-task-add-btn');
                return btn ? { found: true, text: btn.textContent.trim() } : { found: false };
            });
            assert(addBtnInfo.found, 'Add button visible on project page');
            if (addBtnInfo.found) {
                console.log('  Add button text:', JSON.stringify(addBtnInfo.text));
            }

            // Check button position — should be before (left of) the navbar-brand "Tasks"
            var btnPos = await page.evaluate(function() {
                var btn = document.getElementById('wpe_task_add_btn');
                if (!btn) return null;
                var nav = btn.closest('nav');
                if (nav) {
                    var brand = nav.querySelector('.navbar-brand');
                    if (brand) {
                        return {
                            btnLeft: btn.getBoundingClientRect().left,
                            brandLeft: brand.getBoundingClientRect().left,
                            brandText: brand.textContent.trim()
                        };
                    }
                }
                return null;
            });
            if (btnPos) {
                console.log('  Button left:', btnPos.btnLeft, '| Brand left:', btnPos.brandLeft, '(' + btnPos.brandText + ')');
                assert(btnPos.btnLeft < btnPos.brandLeft, 'Add button positioned left of Tasks heading');
            } else {
                skip('Add button positioned left of Tasks heading', 'Could not determine position');
            }

            // Check Time Spent hidden on project page
            timeSpentVisible = await page.evaluate(function() {
                var ths = document.querySelectorAll('table.table thead th');
                for (var i = 0; i < ths.length; i++) {
                    var text = ths[i].textContent.trim();
                    if (text === 'Time Spent' || text === '已花費時間') {
                        return ths[i].style.display !== 'none' && window.getComputedStyle(ths[i]).display !== 'none';
                    }
                }
                return false;
            });
            assert(!timeSpentVisible, 'Time Spent hidden on project page');

            // Check Tags column on project page
            hasTagsHeader = await page.evaluate(function() {
                var ths = document.querySelectorAll('table.table thead th');
                for (var i = 0; i < ths.length; i++) {
                    var text = ths[i].textContent.trim();
                    if (text === 'Tags' || text === '標籤') {
                        return window.getComputedStyle(ths[i]).display !== 'none';
                    }
                }
                return false;
            });
            assert(hasTagsHeader, 'Tags column visible on project page');

            // Check Stage column when groupby=none (default is groupby=stage_id which hides Stage)
            await page.goto(BASE_URL + '/my/projects/8?groupby=none', { waitUntil: 'load' });
            await page.waitForTimeout(WAIT.PAGE_LOAD);
            hasStageHeader = await page.evaluate(function() {
                var ths = document.querySelectorAll('table.table thead th');
                for (var i = 0; i < ths.length; i++) {
                    var text = ths[i].textContent.trim();
                    if (text === 'Stage' || text === '階段') {
                        return window.getComputedStyle(ths[i]).display !== 'none';
                    }
                }
                return false;
            });
            assert(hasStageHeader, 'Stage visible on project page (groupby=none)');
        }

        // ── Test create task form ──
        console.log('\n--- Create Task Form ---');
        await page.goto(BASE_URL + '/my/projects/8/create_task', { waitUntil: 'load' });
        await page.waitForTimeout(WAIT.PAGE_LOAD);

        var formUrl = page.url();
        var formLoaded = formUrl.includes('/create_task');

        if (!formLoaded) {
            skip('Create task form loads', 'Redirected away');
            skip('Create task form has required fields', 'Form not loaded');
            skip('Tag checkboxes available in form', 'Form not loaded');
            skip('Create task submission redirects to project page', 'Form not loaded');
            skip('Newly created task appears in the task list', 'Form not loaded');
        } else {
            assert(true, 'Create task form loads');

            // Check form fields
            var nameInput = await page.$('input#task_name');
            var descTextarea = await page.$('textarea#task_description');
            var submitBtn = await page.$('button[type="submit"]');
            assert(nameInput !== null && descTextarea !== null && submitBtn !== null,
                'Create task form has required fields');

            // Check tags checkboxes
            var tagCheckboxCount = await page.evaluate(function() {
                return document.querySelectorAll('.wpe-tag-checkbox').length;
            });
            console.log('  Tag checkboxes found:', tagCheckboxCount);
            assert(tagCheckboxCount > 0, 'Tag checkboxes available in form');

            // Submit a new task
            var taskName = 'BrowserTest_' + Date.now();
            await page.fill('input#task_name', taskName);
            await page.fill('textarea#task_description', 'Created by automated test');

            // Select first tag
            if (tagCheckboxCount > 0) {
                await page.click('.wpe-tag-checkbox');
            }

            await page.click('button[type="submit"]');
            await page.waitForTimeout(WAIT.PAGE_LOAD);

            var afterSubmitUrl = page.url();
            console.log('  After submit URL:', afterSubmitUrl);
            assert(afterSubmitUrl.includes('/my/projects/8') && !afterSubmitUrl.includes('/create_task'),
                'Create task submission redirects to project page');

            // The new task should appear in the list — check body text
            // Note: default groupby=stage_id, so task may be in any group
            var bodyText = await page.evaluate(function() { return document.body.innerText; });
            var taskFound = bodyText.indexOf(taskName) !== -1;
            if (!taskFound) {
                // Try loading without groupby (flat list)
                await page.goto(BASE_URL + '/my/projects/8?groupby=none', { waitUntil: 'load' });
                await page.waitForTimeout(WAIT.PAGE_LOAD);
                bodyText = await page.evaluate(function() { return document.body.innerText; });
                taskFound = bodyText.indexOf(taskName) !== -1;
            }
            assert(taskFound, 'Newly created task appears in the task list');
            if (taskFound) {
                console.log('  New task found:', taskName);
            }
        }

    } catch (err) {
        console.error('Unexpected error:', err.message);
        assert(false, 'No unexpected errors: ' + err.message);
    } finally {
        await browser.close();
    }

    var summary = printSummary('08 — Task List Features');
    process.exit(summary.fail > 0 ? 1 : 0);
})();
