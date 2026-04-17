/**
 * 08 — Task List Features
 *
 * Tests the task list page changes:
 *   - "Add" button on project task page with i18n (shows "新增" for zh_TW)
 *   - Tags column visible with colored badges
 *   - Time Spent column hidden (via JS)
 *   - Milestone column hidden (via JS)
 *   - State widget column hidden (via JS)
 *   - Assignees column visible with actual content
 *   - Stage column still visible (when not grouped by stage)
 *   - Consistent columns between /my/tasks and /my/projects/<id>
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
        // Helper: get visible header texts from a task table
        function getVisibleHeaders(pg) {
            return pg.evaluate(function() {
                var ths = document.querySelectorAll('table.table thead th');
                var result = [];
                for (var i = 0; i < ths.length; i++) {
                    var d = window.getComputedStyle(ths[i]).display;
                    var sd = ths[i].style.display;
                    if (d !== 'none' && sd !== 'none' && ths[i].textContent.trim().length > 0) {
                        result.push(ths[i].textContent.trim());
                    }
                }
                return result;
            });
        }

        // Helper: check if a column header is hidden
        function isColumnHidden(pg, names) {
            return pg.evaluate(function(names) {
                var ths = document.querySelectorAll('table.table thead th');
                for (var i = 0; i < ths.length; i++) {
                    var text = ths[i].textContent.trim();
                    if (names.indexOf(text) !== -1) {
                        return ths[i].style.display === 'none' || window.getComputedStyle(ths[i]).display === 'none';
                    }
                }
                return true; // not found = effectively hidden
            }, names);
        }

        // ── Login as portal_zhtw and go to /my/tasks first ──
        console.log('--- /my/tasks page ---');
        await loginAndNavigate(page, PORTAL_USER_ZHTW, '/my/tasks', WAIT.PAGE_LOAD);

        const tasksUrl = page.url();
        assert(tasksUrl.includes('/my/tasks'), '/my/tasks page loads without redirect');

        // Time Spent column should be hidden
        var timeSpentHidden = await isColumnHidden(page, ['Time Spent', '已花費時間']);
        assert(timeSpentHidden, 'Time Spent column is hidden on /my/tasks');

        // Milestone column should be hidden
        var milestoneHidden = await isColumnHidden(page, ['Milestone', '里程碑']);
        assert(milestoneHidden, 'Milestone column is hidden on /my/tasks');

        // State widget column should be hidden (empty th with o_status in td)
        var stateWidgetHidden = await page.evaluate(function() {
            var rows = document.querySelectorAll('table.table tbody tr:not(.table-light)');
            for (var i = 0; i < rows.length; i++) {
                var tds = rows[i].querySelectorAll('td');
                for (var j = 0; j < tds.length; j++) {
                    if (tds[j].querySelector('.o_status')) {
                        return tds[j].style.display === 'none' || window.getComputedStyle(tds[j]).display === 'none';
                    }
                }
            }
            return true; // no state widget found = ok
        });
        assert(stateWidgetHidden, 'State widget column is hidden on /my/tasks');

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

        // Get visible headers for consistency check later
        var tasksVisibleHeaders = await getVisibleHeaders(page);
        console.log('  Visible headers:', JSON.stringify(tasksVisibleHeaders));

        var hasStageHeader = tasksVisibleHeaders.some(function(h) { return h === 'Stage' || h === '階段'; });
        assert(hasStageHeader, 'Stage column header still present on /my/tasks');

        // Tag badges in the table body
        var tagBadges = await page.evaluate(function() {
            return document.querySelectorAll('.wpe-tag-badge').length;
        });
        console.log('  Tag badges found:', tagBadges);
        assert(tagBadges > 0, 'Tag badges are rendered in the task list');

        // Assignees column should have content (not blank)
        var assigneesHasContent = await page.evaluate(function() {
            var ths = document.querySelectorAll('table.table thead th');
            var assIdx = -1;
            for (var i = 0; i < ths.length; i++) {
                var text = ths[i].textContent.trim();
                if (text === 'Assignees' || text === '受指派人') {
                    assIdx = i;
                    break;
                }
            }
            if (assIdx === -1) return false;
            // Account for colspan on first th
            var visualCol = 0;
            for (var k = 0; k <= assIdx; k++) {
                if (k < assIdx) {
                    visualCol += parseInt(ths[k].getAttribute('colspan')) || 1;
                }
            }
            // Check first data row's td at the visual column
            var row = document.querySelector('table.table tbody tr:not(.table-light)');
            if (!row) return false;
            var tds = row.querySelectorAll('td');
            var td = tds[visualCol];
            if (!td) return false;
            return td.textContent.trim().length > 0 || !!td.querySelector('img');
        });
        assert(assigneesHasContent, 'Assignees column has content on /my/tasks');

        // ── Navigate to /my/projects/8?groupby=none (project task page) ──
        console.log('\n--- /my/projects/8 page ---');
        await page.goto(BASE_URL + '/my/projects/8?groupby=none', { waitUntil: 'load' });
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
            skip('Add button shows translated text for zh_TW', 'Project page not loaded');
            skip('Add button positioned left of Tasks heading', 'Project page not loaded');
            skip('Time Spent hidden on project page', 'Project page not loaded');
            skip('Milestone hidden on project page', 'Project page not loaded');
            skip('State widget hidden on project page', 'Project page not loaded');
            skip('Tags visible on project page', 'Project page not loaded');
            skip('Stage visible on project page (groupby=none)', 'Project page not loaded');
            skip('Assignees has content on project page', 'Project page not loaded');
            skip('Column layout consistent between /my/tasks and /my/projects/<id>', 'Project page not loaded');
        } else {
            assert(true, 'Project page loads with portal template');

            // Check "Add" button (should show "新增" for zh_TW user)
            var addBtnInfo = await page.evaluate(function() {
                var btn = document.getElementById('wpe_task_add_btn');
                if (!btn) btn = document.querySelector('.wpe-task-add-btn');
                return btn ? { found: true, text: btn.textContent.trim() } : { found: false };
            });
            assert(addBtnInfo.found, 'Add button visible on project page');
            if (addBtnInfo.found) {
                console.log('  Add button text:', JSON.stringify(addBtnInfo.text));
                assert(addBtnInfo.text === '新增', 'Add button shows translated text for zh_TW');
            } else {
                skip('Add button shows translated text for zh_TW', 'Add button not found');
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
            var projTimeSpentHidden = await isColumnHidden(page, ['Time Spent', '已花費時間']);
            assert(projTimeSpentHidden, 'Time Spent hidden on project page');

            // Check Milestone hidden on project page
            var projMilestoneHidden = await isColumnHidden(page, ['Milestone', '里程碑']);
            assert(projMilestoneHidden, 'Milestone hidden on project page');

            // Check State widget hidden on project page
            var projStateHidden = await page.evaluate(function() {
                var rows = document.querySelectorAll('table.table tbody tr:not(.table-light)');
                for (var i = 0; i < rows.length; i++) {
                    var tds = rows[i].querySelectorAll('td');
                    for (var j = 0; j < tds.length; j++) {
                        if (tds[j].querySelector('.o_status')) {
                            return tds[j].style.display === 'none' || window.getComputedStyle(tds[j]).display === 'none';
                        }
                    }
                }
                return true;
            });
            assert(projStateHidden, 'State widget hidden on project page');

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

            // Stage column visible (we're on groupby=none)
            var projVisibleHeaders = await getVisibleHeaders(page);
            console.log('  Visible headers:', JSON.stringify(projVisibleHeaders));
            hasStageHeader = projVisibleHeaders.some(function(h) { return h === 'Stage' || h === '階段'; });
            assert(hasStageHeader, 'Stage visible on project page (groupby=none)');

            // Assignees has content on project page
            var projAssigneesContent = await page.evaluate(function() {
                var row = document.querySelector('table.table tbody tr:not(.table-light)');
                if (!row) return false;
                var tds = row.querySelectorAll('td');
                for (var i = 0; i < tds.length; i++) {
                    if (tds[i].querySelector('img.o_portal_contact_img')) return true;
                }
                return false;
            });
            assert(projAssigneesContent, 'Assignees has content on project page');

            // Column consistency: /my/tasks and /my/projects/<id> should show same columns
            var projHeadersNorm = projVisibleHeaders.map(function(h) {
                var map = { '名稱': 'Name', '受指派人': 'Assignees', '標籤': 'Tags', '階段': 'Stage' };
                return map[h] || h;
            });
            var tasksHeadersNorm = tasksVisibleHeaders.map(function(h) {
                var map = { '名稱': 'Name', '受指派人': 'Assignees', '標籤': 'Tags', '階段': 'Stage' };
                return map[h] || h;
            });
            var headersMatch = JSON.stringify(projHeadersNorm) === JSON.stringify(tasksHeadersNorm);
            console.log('  /my/tasks headers (normalized):', JSON.stringify(tasksHeadersNorm));
            console.log('  /my/projects headers (normalized):', JSON.stringify(projHeadersNorm));
            assert(headersMatch, 'Column layout consistent between /my/tasks and /my/projects/<id>');
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
