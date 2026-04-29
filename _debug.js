async page => {
  return await page.evaluate(function() {
    var sb = document.querySelector('.wpu-search-bar');
    if (!sb) return {error: 'no .wpu-search-bar element found'};

    // Check if spacer was created (proof initFixedBars ran)
    var spacer = sb.nextElementSibling;
    var spacerIsOurs = spacer && spacer.classList.contains('wpu-scroll-spacer');

    // Check computed styles
    var cs = window.getComputedStyle(sb);

    // Check all ancestors for overflow issues
    var ancestors = [];
    var el = sb.parentElement;
    while (el && el !== document.documentElement) {
      var s = window.getComputedStyle(el);
      ancestors.push({
        tag: el.tagName,
        id: el.id || '',
        cls: el.className.toString().substring(0, 50),
        overflow: s.overflow,
        overflowY: s.overflowY,
        position: s.position,
        height: s.height
      });
      el = el.parentElement;
    }

    // Check if header exists (for navbar height calculation)
    var header = document.querySelector('header');
    var headerHeight = header ? header.getBoundingClientRect().height : 'no header';

    // Check the actual JS bundle for our function
    var scripts = document.querySelectorAll('script[src*="assets"]');
    var scriptUrls = [];
    scripts.forEach(function(s) { scriptUrls.push(s.src); });

    return {
      searchBar: {
        position: cs.position,
        hasStuckClass: sb.classList.contains('wpu-stuck'),
        classList: sb.className,
        top: cs.top,
        zIndex: cs.zIndex
      },
      spacerFound: spacerIsOurs,
      spacerDisplay: spacerIsOurs ? spacer.style.display : 'n/a',
      headerHeight: headerHeight,
      scrollY: window.scrollY,
      bodyScrollHeight: document.body.scrollHeight,
      viewportHeight: window.innerHeight,
      ancestors: ancestors,
      scriptCount: scriptUrls.length,
      scriptUrls: scriptUrls.map(function(u) { return u.split('/').pop(); })
    };
  });
}
