async page => {
  return await page.evaluate(function() {
    // Check all loaded CSS and JS asset URLs and their cache hashes
    var cssLinks = document.querySelectorAll('link[rel="stylesheet"]');
    var jsScripts = document.querySelectorAll('script[src]');

    var css = [];
    cssLinks.forEach(function(l) {
      if (l.href.indexOf('assets') !== -1) {
        css.push(l.href);
      }
    });

    var js = [];
    jsScripts.forEach(function(s) {
      if (s.src.indexOf('assets') !== -1) {
        js.push(s.src);
      }
    });

    // Check if our JS function exists in the loaded code
    // by checking if setupStickyOnScroll function name exists
    var hasNewJS = typeof window.__wpuStickyCheck === 'undefined';

    // Check the actual content of our search bar CSS rule
    var searchBarRules = [];
    var sheets = document.styleSheets;
    for (var i = 0; i < sheets.length; i++) {
      try {
        var rules = sheets[i].cssRules;
        for (var j = 0; j < rules.length; j++) {
          if (rules[j].selectorText === '.wpu-search-bar') {
            searchBarRules.push({
              file: sheets[i].href ? sheets[i].href.match(/\/([^\/]+)$/)[1] : 'inline',
              cssText: rules[j].cssText
            });
          }
          if (rules[j].selectorText === '.wpu-search-bar.wpu-stuck') {
            searchBarRules.push({
              file: sheets[i].href ? sheets[i].href.match(/\/([^\/]+)$/)[1] : 'inline',
              cssText: rules[j].cssText
            });
          }
        }
      } catch(e) {}
    }

    return {
      cssAssets: css,
      jsAssets: js,
      searchBarRules: searchBarRules
    };
  });
}
