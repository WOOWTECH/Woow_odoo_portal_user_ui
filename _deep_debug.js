async page => {
  // DEEP DEBUG: Check everything from scratch
  var result = await page.evaluate(function() {
    var sb = document.querySelector('.wpu-search-bar');
    if (!sb) return {error: 'no search bar'};

    // 1. Does our scroll listener exist? Count scroll listeners
    // We can't directly count, but we can test if scrolling triggers our code
    var beforeScrollY = window.scrollY;

    // 2. Check the ACTUAL CSS applied to .wpu-search-bar from ALL stylesheets
    var matchedRules = [];
    try {
      var sheets = document.styleSheets;
      for (var i = 0; i < sheets.length; i++) {
        try {
          var rules = sheets[i].cssRules;
          for (var j = 0; j < rules.length; j++) {
            var r = rules[j];
            if (r.selectorText && r.selectorText.indexOf('wpu-search-bar') !== -1) {
              matchedRules.push({
                selector: r.selectorText,
                position: r.style.position || '',
                top: r.style.top || '',
                display: r.style.display || '',
                cssText: r.cssText.substring(0, 200)
              });
            }
          }
        } catch(e) {}
      }
    } catch(e) {}

    // 3. Check if maybe Odoo's own code is overwriting our styles
    // Look for any inline styles
    var inlineStyle = sb.getAttribute('style') || 'none';

    // 4. Check the ACTUAL HTML structure around search bar
    var prevSibling = sb.previousElementSibling;
    var nextSibling = sb.nextElementSibling;

    // 5. Check if maybe the Odoo livechat widget or other widgets are
    // adding position:fixed elements that conflict
    var fixedElements = [];
    var allEls = document.querySelectorAll('*');
    for (var k = 0; k < allEls.length; k++) {
      var pos = window.getComputedStyle(allEls[k]).position;
      if (pos === 'fixed' || pos === 'sticky') {
        fixedElements.push({
          tag: allEls[k].tagName,
          cls: (allEls[k].className || '').toString().substring(0, 60),
          id: allEls[k].id || '',
          pos: pos,
          top: window.getComputedStyle(allEls[k]).top,
          zIndex: window.getComputedStyle(allEls[k]).zIndex
        });
      }
    }

    return {
      matchedRules: matchedRules,
      inlineStyle: inlineStyle,
      prevSibling: prevSibling ? prevSibling.className.substring(0, 60) : 'none',
      nextSibling: nextSibling ? nextSibling.className.substring(0, 60) : 'none',
      fixedElements: fixedElements,
      spacerExists: nextSibling ? nextSibling.classList.contains('wpu-scroll-spacer') : false
    };
  });

  // Now scroll and verify behavior
  await page.evaluate(function() { window.scrollTo(0, 300); });
  await page.waitForTimeout(600);

  var afterScroll = await page.evaluate(function() {
    var sb = document.querySelector('.wpu-search-bar');
    return {
      scrollY: window.scrollY,
      stuck: sb.classList.contains('wpu-stuck'),
      position: window.getComputedStyle(sb).position,
      inlineStyle: sb.getAttribute('style') || 'none',
      rectTop: sb.getBoundingClientRect().top,
      rectBottom: sb.getBoundingClientRect().bottom
    };
  });

  await page.screenshot({ path: '_deep_scrolled.png' });

  return { initial: result, afterScroll: afterScroll };
}
