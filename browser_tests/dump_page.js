const { chromium } = require('playwright');
(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    
    const url = new URL('http://localhost:9097');
    await page.context().addCookies([{
        name: 'frontend_lang', value: 'en_US',
        domain: url.hostname, path: '/',
    }]);
    await page.goto('http://localhost:9097/web/login', { waitUntil: 'load' });
    await page.waitForTimeout(500);
    await page.fill('input[name="login"]', 'portal_zhtw');
    await page.fill('input[name="password"]', 'portal_zhtw');
    await page.click('.oe_login_form button[type="submit"]');
    await page.waitForTimeout(5000);
    
    await page.goto('http://localhost:9097/my/projects/8', { waitUntil: 'load' });
    await page.waitForTimeout(3000);
    
    // Get the searchbar/nav area  
    const searchbarHtml = await page.evaluate(() => {
        const searchbar = document.querySelector('.o_portal_search_panel, nav.navbar');
        return searchbar ? searchbar.outerHTML.substring(0, 2000) : 'No searchbar found';
    });
    console.log('=== SEARCHBAR/NAV HTML ===');
    console.log(searchbarHtml);
    
    // Check if add button exists anywhere in page
    const addBtnSearch = await page.evaluate(() => {
        const btn = document.getElementById('wpe_task_add_btn');
        const btnByClass = document.querySelector('.wpe-task-add-btn');
        const allBtns = document.querySelectorAll('a[href*="create_task"]');
        return {
            byId: btn ? btn.outerHTML : null,
            byClass: btnByClass ? btnByClass.outerHTML : null,
            byHref: Array.from(allBtns).map(b => b.outerHTML),
        };
    });
    console.log('\n=== ADD BUTTON SEARCH ===');
    console.log(JSON.stringify(addBtnSearch, null, 2));
    
    // Get table headers 
    const tableInfo = await page.evaluate(() => {
        const table = document.querySelector('table.table');
        if (!table) return 'No table found';
        const ths = table.querySelectorAll('thead th');
        return {
            headerCount: ths.length,
            headers: Array.from(ths).map(th => ({
                text: th.textContent.trim(),
                display: window.getComputedStyle(th).display,
                classes: th.className,
            })),
        };
    });
    console.log('\n=== TABLE HEADERS ===');
    console.log(JSON.stringify(tableInfo, null, 2));
    
    // Get task names in the list
    const tasks = await page.evaluate(() => {
        const rows = document.querySelectorAll('table.table tbody tr');
        return Array.from(rows).map(r => {
            const nameCell = r.querySelector('td:nth-child(2), td a');
            return nameCell ? nameCell.textContent.trim().substring(0, 80) : '';
        }).filter(t => t.length > 0);
    });
    console.log('\n=== TASKS IN LIST ===');
    console.log(JSON.stringify(tasks, null, 2));
    
    await browser.close();
})();
