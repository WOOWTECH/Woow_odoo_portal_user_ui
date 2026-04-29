async page => {
  return await page.evaluate(function() {
    // Check ALL header-like elements
    var headers = [];
    var headerEl = document.querySelector('header');
    if (headerEl) {
      headers.push({
        selector: 'header',
        tag: headerEl.tagName,
        cls: headerEl.className.substring(0, 80),
        height: headerEl.getBoundingClientRect().height,
        position: window.getComputedStyle(headerEl).position,
        children: headerEl.children.length
      });
    }

    var navbars = document.querySelectorAll('nav.navbar, .o_portal_navbar, .o_navbar');
    navbars.forEach(function(n) {
      headers.push({
        selector: 'nav',
        tag: n.tagName,
        cls: n.className.substring(0, 80),
        height: n.getBoundingClientRect().height,
        position: window.getComputedStyle(n).position
      });
    });

    // Check if there's a breadcrumb navbar between header and content
    var portalNavbar = document.querySelector('.o_portal_navbar');
    var breadcrumbInfo = null;
    if (portalNavbar) {
      breadcrumbInfo = {
        cls: portalNavbar.className.substring(0, 80),
        height: portalNavbar.getBoundingClientRect().height,
        position: window.getComputedStyle(portalNavbar).position,
        bottom: portalNavbar.getBoundingClientRect().bottom
      };
    }

    // What is the actual gap between header bottom and search bar top?
    var sb = document.querySelector('.wpu-search-bar');
    var sbTop = sb ? sb.getBoundingClientRect().top : 'n/a';
    var headerBottom = headerEl ? headerEl.getBoundingClientRect().bottom : 'n/a';

    return {
      headers: headers,
      breadcrumb: breadcrumbInfo,
      searchBarTop: sbTop,
      headerBottom: headerBottom,
      gapBetween: (typeof sbTop === 'number' && typeof headerBottom === 'number') ? sbTop - headerBottom : 'n/a',
      url: window.location.href,
      userAgent: navigator.userAgent,
      viewport: { w: window.innerWidth, h: window.innerHeight }
    };
  });
}
