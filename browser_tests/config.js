/**
 * Woow Portal Enhanced - Browser Test Configuration
 * Shared constants and helpers for all Playwright test scripts.
 */

const BASE_URL = process.env.ODOO_URL || 'http://localhost:9097';
const PORTAL_USER = { login: 'portal', password: 'portal' };
const PORTAL_USER_ZHTW = { login: 'portal_zhtw', password: 'portal_zhtw' };
const ADMIN_USER  = { login: 'admin',  password: 'admin'  };

// Mobile viewport (iPhone 14-class)
const MOBILE_VP = { width: 390, height: 844 };
// Desktop viewport
const DESKTOP_VP = { width: 1280, height: 800 };

// Wait durations
const WAIT = {
    PAGE_LOAD: 3000,
    LOGIN: 5000,
    SHORT: 500,
    ANIMATION: 400,
    DEBOUNCE: 500,
};

// Colors
const THEME_BLUE = 'rgb(46, 134, 193)';   // #2E86C1
const DEEP_GRAY  = 'rgb(33, 33, 33)';     // #212121
const WHITE      = 'rgb(255, 255, 255)';

// --- Helpers ---

let passCount = 0;
let failCount = 0;
let skipCount = 0;
const results = [];

function assert(condition, testName) {
    if (condition) {
        passCount++;
        results.push({ status: 'PASS', name: testName });
        console.log(`  \x1b[32mPASS\x1b[0m  ${testName}`);
    } else {
        failCount++;
        results.push({ status: 'FAIL', name: testName });
        console.log(`  \x1b[31mFAIL\x1b[0m  ${testName}`);
    }
}

function skip(testName, reason) {
    skipCount++;
    results.push({ status: 'SKIP', name: testName, reason });
    console.log(`  \x1b[33mSKIP\x1b[0m  ${testName} (${reason})`);
}

function printSummary(suiteName) {
    const total = passCount + failCount + skipCount;
    console.log(`\n${'='.repeat(60)}`);
    console.log(`  ${suiteName} - Summary`);
    console.log(`${'='.repeat(60)}`);
    console.log(`  Total: ${total}  |  \x1b[32mPass: ${passCount}\x1b[0m  |  \x1b[31mFail: ${failCount}\x1b[0m  |  \x1b[33mSkip: ${skipCount}\x1b[0m`);
    if (failCount > 0) {
        console.log(`\n  Failed tests:`);
        results.filter(r => r.status === 'FAIL').forEach(r => {
            console.log(`    - ${r.name}`);
        });
    }
    console.log(`${'='.repeat(60)}\n`);
    return { total, pass: passCount, fail: failCount, skip: skipCount, results };
}

function resetCounters() {
    passCount = 0;
    failCount = 0;
    skipCount = 0;
    results.length = 0;
}

/**
 * Login to Odoo portal and navigate to a target page.
 *
 * A ``frontend_lang=en_US`` cookie is pre-set before the login page
 * loads.  This prevents Odoo's http_routing ``_match()`` from
 * redirecting non-default-language users to ``/<lang>/...`` URLs
 * (which are unroutable without the ``website`` module).
 */
async function loginAndNavigate(page, user, targetPath, extraWait) {
    const url = new URL(BASE_URL);
    await page.context().addCookies([{
        name: 'frontend_lang',
        value: 'en_US',
        domain: url.hostname,
        path: '/',
    }]);
    await page.goto(`${BASE_URL}/web/login`, { waitUntil: 'load' });
    await page.waitForTimeout(WAIT.SHORT);
    await page.fill('input[name="login"]', user.login);
    await page.fill('input[name="password"]', user.password);
    await page.click('.oe_login_form button[type="submit"], .oe_login_form .btn-primary');
    await page.waitForTimeout(WAIT.LOGIN);
    if (targetPath) {
        await page.goto(`${BASE_URL}${targetPath}`, { waitUntil: 'load' });
        await page.waitForTimeout(extraWait || WAIT.PAGE_LOAD);
    }
}

/**
 * Parse an rgb(r, g, b) string into [r, g, b] array.
 */
function parseRgb(str) {
    const m = (str || '').match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (!m) return null;
    return [parseInt(m[1]), parseInt(m[2]), parseInt(m[3])];
}

/**
 * Check if two rgb strings refer to the same color (with tolerance).
 */
function colorsMatch(a, b, tolerance) {
    tolerance = tolerance || 5;
    const ca = parseRgb(a);
    const cb = parseRgb(b);
    if (!ca || !cb) return false;
    return Math.abs(ca[0] - cb[0]) <= tolerance
        && Math.abs(ca[1] - cb[1]) <= tolerance
        && Math.abs(ca[2] - cb[2]) <= tolerance;
}

module.exports = {
    BASE_URL, PORTAL_USER, PORTAL_USER_ZHTW, ADMIN_USER,
    MOBILE_VP, DESKTOP_VP, WAIT,
    THEME_BLUE, DEEP_GRAY, WHITE,
    assert, skip, printSummary, resetCounters,
    loginAndNavigate, parseRgb, colorsMatch,
    get failCount() { return failCount; },
};
