async page => {
  // 1. Check if the inline script is present
  const inlineScriptPresent = await page.evaluate(() => {
    const scripts = document.querySelectorAll('script');
    let found = false;
    scripts.forEach(s => {
      if (s.textContent.includes('wpuSticky')) found = true;
    });
    return found;
  });

  // 2. Check search bar initial state
  const searchBar = await page.evaluate(() => {
    const sb = document.getElementById('wpu_search_bar') || document.querySelector('.wpu-search-bar');
    if (!sb) return { found: false };
    const cs = window.getComputedStyle(sb);
    // Check for spacer div (created by inline script)
    let spacer = sb.nextElementSibling;
    let hasSpacerFromInline = false;
    while (spacer) {
      if (spacer.tagName === 'DIV' && spacer.style.display === 'none' && spacer.style.height) {
        hasSpacerFromInline = true;
        break;
      }
      if (spacer.tagName === 'SCRIPT') { spacer = spacer.nextElementSibling; continue; }
      break;
    }
    return {
      found: true,
      id: sb.id,
      position: cs.position,
      hasStuck: sb.classList.contains('wpu-stuck'),
      top: sb.getBoundingClientRect().top,
      hasSpacerFromInline: hasSpacerFromInline
    };
  });

  // 3. Scroll down
  await page.evaluate(() => window.scrollTo(0, 300));
  await page.waitForTimeout(500);

  const afterScroll = await page.evaluate(() => {
    const sb = document.getElementById('wpu_search_bar') || document.querySelector('.wpu-search-bar');
    if (!sb) return { found: false };
    const cs = window.getComputedStyle(sb);
    return {
      position: cs.position,
      hasStuck: sb.classList.contains('wpu-stuck'),
      top: sb.getBoundingClientRect().top,
      topStyle: sb.style.top,
      zIndex: cs.zIndex
    };
  });

  // 4. Scroll back up
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(300);

  const afterScrollBack = await page.evaluate(() => {
    const sb = document.getElementById('wpu_search_bar') || document.querySelector('.wpu-search-bar');
    if (!sb) return { found: false };
    const cs = window.getComputedStyle(sb);
    return {
      position: cs.position,
      hasStuck: sb.classList.contains('wpu-stuck'),
      top: sb.getBoundingClientRect().top
    };
  });

  return {
    inlineScriptPresent,
    searchBar,
    afterScroll,
    afterScrollBack,
    verdict: inlineScriptPresent && afterScroll.hasStuck && afterScroll.position === 'fixed' && !afterScrollBack.hasStuck
      ? 'PASS: Inline sticky script works correctly'
      : 'FAIL: Something is wrong'
  };
}
