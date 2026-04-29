async page => {
  return await page.evaluate(() => {
    var el = document.querySelector('.wpu-notif-sticky-top');
    if (!el) return { error: 'no element' };
    var siblings = [];
    var sib = el.nextElementSibling;
    var i = 0;
    while (sib && i < 10) {
      siblings.push({
        tag: sib.tagName,
        cls: sib.className.substring(0, 50),
        display: sib.style.display,
        height: sib.style.height,
        id: sib.id || ''
      });
      sib = sib.nextElementSibling;
      i++;
    }
    return {
      dataAttr: el.dataset.wpuStickyInit,
      siblings: siblings
    };
  });
}
