const { chromium } = require('playwright');
const { BASE_URL, PORTAL_USER_ZHTW, DESKTOP_VP, WAIT, loginAndNavigate } = require('./config');

(async () => {
    const browser = await chromium.launch({ headless: true });
    var ctx = await browser.newContext({ viewport: DESKTOP_VP });
    var page = await ctx.newPage();
    await loginAndNavigate(page, PORTAL_USER_ZHTW, '/my/projects/8?groupby=none', WAIT.PAGE_LOAD);

    // Dump ALL th with index, outerHTML, display
    var headerInfo = await page.evaluate(function() {
        var ths = document.querySelectorAll('table.table thead th');
        return Array.from(ths).map(function(th, i) {
            return {
                idx: i,
                text: th.textContent.trim(),
                styleDisplay: th.style.display,
                computedDisplay: window.getComputedStyle(th).display,
                html: th.outerHTML.substring(0, 200)
            };
        });
    });
    console.log('=== ALL HEADERS ===');
    headerInfo.forEach(function(h) {
        console.log('  [' + h.idx + '] "' + h.text + '" style=' + h.styleDisplay + ' computed=' + h.computedDisplay);
        console.log('      HTML: ' + h.html);
    });

    // Dump first data row td details
    var rowInfo = await page.evaluate(function() {
        var row = document.querySelector('table.table tbody tr:not(.table-light)');
        if (!row) return [];
        var cells = row.querySelectorAll('td');
        return Array.from(cells).map(function(td, i) {
            var hasOStatus = !!td.querySelector('.o_status, .fa-check-circle, .fa-times-circle, .fa-hourglass-o');
            return {
                idx: i,
                text: td.textContent.trim().substring(0, 60),
                styleDisplay: td.style.display,
                hasImg: !!td.querySelector('img'),
                hasOStatus: hasOStatus,
                html: td.outerHTML.substring(0, 300)
            };
        });
    });
    console.log('\n=== FIRST ROW CELLS ===');
    rowInfo.forEach(function(c) {
        console.log('  [' + c.idx + '] "' + c.text + '" style=' + c.styleDisplay + ' img=' + c.hasImg + ' oStatus=' + c.hasOStatus);
        console.log('      HTML: ' + c.html);
    });

    await browser.close();
})();
