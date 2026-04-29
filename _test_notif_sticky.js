async page => {
  // 1. Check inline script present
  const inlineScriptPresent = await page.evaluate(() => {
    const scripts = document.querySelectorAll('script');
    let found = false;
    scripts.forEach(s => {
      if (s.textContent.includes('wpuSticky')) found = true;
    });
    return found;
  });

  // 2. Check notif sticky top initial state
  const initial = await page.evaluate(() => {
    var el = document.querySelector('.wpu-notif-sticky-top');
    if (!el) return { found: false };
    var cs = window.getComputedStyle(el);
    return {
      found: true,
      position: cs.position,
      hasStuck: el.classList.contains('wpu-stuck'),
      top: el.getBoundingClientRect().top,
      hasStickyInit: el.dataset.wpuStickyInit === '1'
    };
  });

  // 3. Scroll down
  await page.evaluate(() => window.scrollTo(0, 400));
  await page.waitForTimeout(500);

  const afterScroll = await page.evaluate(() => {
    var el = document.querySelector('.wpu-notif-sticky-top');
    if (!el) return { found: false };
    var cs = window.getComputedStyle(el);
    return {
      position: cs.position,
      hasStuck: el.classList.contains('wpu-stuck'),
      top: el.getBoundingClientRect().top,
      topStyle: el.style.top
    };
  });

  // 4. Scroll back
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(300);

  const afterScrollBack = await page.evaluate(() => {
    var el = document.querySelector('.wpu-notif-sticky-top');
    if (!el) return { found: false };
    var cs = window.getComputedStyle(el);
    return {
      position: cs.position,
      hasStuck: el.classList.contains('wpu-stuck')
    };
  });

  // 5. Check spacer count
  const spacers = await page.evaluate(() => {
    var el = document.querySelector('.wpu-notif-sticky-top');
    if (!el) return { count: 0 };
    var count = 0;
    var sib = el.nextElementSibling;
    while (sib) {
      if (sib.tagName === 'SCRIPT') { sib = sib.nextElementSibling; continue; }
      if (sib.tagName === 'DIV' && sib.style.height) { count++; sib = sib.nextElementSibling; continue; }
      break;
    }
    return { count: count, wpuScrollSpacers: document.querySelectorAll('.wpu-scroll-spacer').length };
  });

  return {
    inlineScriptPresent,
    initial,
    afterScroll,
    afterScrollBack,
    spacers,
    verdict: inlineScriptPresent && afterScroll.hasStuck && afterScroll.position === 'fixed' && !afterScrollBack.hasStuck && spacers.count <= 1
      ? 'PASS'
      : 'FAIL'
  };
}
