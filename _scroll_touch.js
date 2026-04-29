async page => {
  // Test 1: Scroll using JS and check
  await page.evaluate(function() { window.scrollTo(0, 300); });
  await page.waitForTimeout(500);

  var test1 = await page.evaluate(function() {
    var sb = document.querySelector('.wpu-search-bar');
    return {
      method: 'window.scrollTo',
      scrollY: window.scrollY,
      position: window.getComputedStyle(sb).position,
      stuck: sb.classList.contains('wpu-stuck'),
      top: sb.getBoundingClientRect().top
    };
  });

  // Reset
  await page.evaluate(function() { window.scrollTo(0, 0); });
  await page.waitForTimeout(300);

  // Test 2: Scroll using mouse wheel (simulates real interaction)
  await page.mouse.wheel(0, 500);
  await page.waitForTimeout(800);

  var test2 = await page.evaluate(function() {
    var sb = document.querySelector('.wpu-search-bar');
    return {
      method: 'mouse.wheel',
      scrollY: window.scrollY,
      position: window.getComputedStyle(sb).position,
      stuck: sb.classList.contains('wpu-stuck'),
      top: sb.getBoundingClientRect().top
    };
  });

  // Reset
  await page.evaluate(function() { window.scrollTo(0, 0); });
  await page.waitForTimeout(300);

  // Test 3: Touch swipe simulation
  await page.touchscreen.tap(195, 600);
  await page.waitForTimeout(100);

  // Simulate touch scroll: finger starts at y=600, drags to y=200
  await page.evaluate(function() {
    var startY = 600;
    var endY = 200;
    var el = document.elementFromPoint(195, startY);

    var touchStart = new TouchEvent('touchstart', {
      touches: [new Touch({identifier: 0, target: el, clientX: 195, clientY: startY})],
      bubbles: true
    });
    var touchMove = new TouchEvent('touchmove', {
      touches: [new Touch({identifier: 0, target: el, clientX: 195, clientY: endY})],
      bubbles: true
    });
    var touchEnd = new TouchEvent('touchend', {
      touches: [],
      changedTouches: [new Touch({identifier: 0, target: el, clientX: 195, clientY: endY})],
      bubbles: true
    });

    el.dispatchEvent(touchStart);
    el.dispatchEvent(touchMove);
    el.dispatchEvent(touchEnd);
  });
  await page.waitForTimeout(500);

  var test3 = await page.evaluate(function() {
    var sb = document.querySelector('.wpu-search-bar');
    return {
      method: 'touchEvent dispatch',
      scrollY: window.scrollY,
      position: window.getComputedStyle(sb).position,
      stuck: sb.classList.contains('wpu-stuck'),
      top: sb.getBoundingClientRect().top
    };
  });

  // Take screenshot of test1 result (scroll down again)
  await page.evaluate(function() { window.scrollTo(0, 300); });
  await page.waitForTimeout(500);
  await page.screenshot({ path: '_debug_scrolled.png' });

  return { test1: test1, test2: test2, test3: test3 };
}
