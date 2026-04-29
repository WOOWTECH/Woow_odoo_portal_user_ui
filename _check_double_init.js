async page => {
  return await page.evaluate(() => {
    var sb = document.getElementById('wpu_search_bar');
    if (!sb) return { error: 'no search bar' };
    // Count spacer divs adjacent to search bar
    var spacers = 0;
    var el = sb.nextElementSibling;
    while (el) {
      if (el.tagName === 'SCRIPT') { el = el.nextElementSibling; continue; }
      if (el.tagName === 'DIV' && el.style.height) { spacers++; el = el.nextElementSibling; continue; }
      break;
    }
    // Also check for .wpu-scroll-spacer elements anywhere
    var scrollSpacers = document.querySelectorAll('.wpu-scroll-spacer');
    return {
      adjacentSpacerCount: spacers,
      wpuScrollSpacerCount: scrollSpacers.length,
      scrollY: window.pageYOffset
    };
  });
}
