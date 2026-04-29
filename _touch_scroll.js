async page => {
  // Screenshot before scroll
  await page.screenshot({ path: '_mobile_before.png' });

  // Simulate real touch scroll: finger at center, drag up 400px
  await page.touchscreen.tap(195, 400);
  await page.waitForTimeout(200);

  // Use real mouse wheel as well for testing
  await page.mouse.wheel(0, 400);
  await page.waitForTimeout(800);

  var afterWheel = await page.evaluate(function() {
    var sb = document.querySelector('.wpu-search-bar');
    return {
      scrollY: window.scrollY,
      position: window.getComputedStyle(sb).position,
      stuck: sb.classList.contains('wpu-stuck'),
      rectTop: sb.getBoundingClientRect().top,
      styleTop: sb.style.top
    };
  });

  await page.screenshot({ path: '_mobile_after_wheel.png' });

  // Now check: does our scroll handler fire at ALL?
  // Inject a test to see
  var handlerTest = await page.evaluate(function() {
    return new Promise(function(resolve) {
      var detected = false;
      var origHandler = null;

      // Check if there IS a scroll handler by manually scrolling
      window.scrollTo(0, 0);

      // Wait a bit then scroll
      setTimeout(function() {
        window.addEventListener('scroll', function testHandler() {
          detected = true;
          window.removeEventListener('scroll', testHandler);
        }, {once: true});

        window.scrollTo(0, 300);

        setTimeout(function() {
          var sb = document.querySelector('.wpu-search-bar');
          resolve({
            scrollEventFired: detected,
            scrollY: window.scrollY,
            stuck: sb.classList.contains('wpu-stuck'),
            position: window.getComputedStyle(sb).position,
            rectTop: sb.getBoundingClientRect().top
          });
        }, 300);
      }, 200);
    });
  });

  await page.screenshot({ path: '_mobile_after_js.png' });

  return { afterWheel: afterWheel, handlerTest: handlerTest };
}
