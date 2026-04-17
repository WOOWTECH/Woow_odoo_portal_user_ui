const { chromium } = require('playwright');
const { BASE_URL, PORTAL_USER_ZHTW, PORTAL_USER, DESKTOP_VP, WAIT, loginAndNavigate } = require('./config');

(async () => {
    const browser = await chromium.launch({ headless: true });

    // ---- Test with zh_TW user ----
    console.log('=== zh_TW user ===');
    var ctx = await browser.newContext({ viewport: DESKTOP_VP });
    var page = await ctx.newPage();
    await loginAndNavigate(page, PORTAL_USER_ZHTW, '/my/projects/8?groupby=none', WAIT.PAGE_LOAD);

    console.log('URL:', page.url());

    // Get all visible headers
    var visHeaders = await page.evaluate(function() {
        var ths = document.querySelectorAll('table.table thead th');
        var result = [];
        for (var i = 0; i < ths.length; i++) {
            var d = window.getComputedStyle(ths[i]).display;
            var sd = ths[i].style.display;
            var text = ths[i].textContent.trim();
            result.push({ idx: i, text: text || '(empty)', visible: d !== 'none' && sd !== 'none', display: d, styleDisplay: sd });
        }
        return result;
    });
    console.log('Headers (all):', JSON.stringify(visHeaders, null, 2));

    var visible = visHeaders.filter(function(h) { return h.visible; });
    console.log('Visible headers:', visible.map(function(h) { return h.text; }));

    // Check Add button
    var addBtn = await page.evaluate(function() {
        var btn = document.getElementById('wpe_task_add_btn');
        return btn ? { text: btn.textContent.trim(), visible: true } : { visible: false };
    });
    console.log('Add button:', JSON.stringify(addBtn));

    // Check Assignees column content
    var assigneesData = await page.evaluate(function() {
        var rows = document.querySelectorAll('table.table tbody tr:not(.table-light)');
        var result = [];
        for (var i = 0; i < Math.min(rows.length, 3); i++) {
            var tds = rows[i].querySelectorAll('td');
            // Find the assignees td (index 3 in base template: #, priority, name, assignees)
            var items = [];
            for (var j = 0; j < tds.length; j++) {
                var text = tds[j].textContent.trim();
                var display = tds[j].style.display;
                if (display !== 'none') {
                    items.push(text.substring(0, 40));
                }
            }
            result.push(items);
        }
        return result;
    });
    console.log('First rows (visible td content):', JSON.stringify(assigneesData, null, 2));

    await ctx.close();

    // ---- Test with en_US user ----
    console.log('\n=== en_US user ===');
    ctx = await browser.newContext({ viewport: DESKTOP_VP });
    page = await ctx.newPage();
    await loginAndNavigate(page, PORTAL_USER, '/my/tasks', WAIT.PAGE_LOAD);

    console.log('URL:', page.url());

    var enHeaders = await page.evaluate(function() {
        var ths = document.querySelectorAll('table.table thead th');
        var result = [];
        for (var i = 0; i < ths.length; i++) {
            var d = window.getComputedStyle(ths[i]).display;
            var sd = ths[i].style.display;
            if (d !== 'none' && sd !== 'none') {
                result.push(ths[i].textContent.trim() || '(empty)');
            }
        }
        return result;
    });
    console.log('Visible headers:', enHeaders);

    var enAddBtn = await page.evaluate(function() {
        var btn = document.getElementById('wpe_task_add_btn');
        return btn ? { text: btn.textContent.trim() } : null;
    });
    console.log('Add button:', JSON.stringify(enAddBtn));

    await browser.close();
})();
