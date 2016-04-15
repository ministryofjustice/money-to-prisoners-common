// Focus on search input field
/* globals exports, require  */
'use strict';

var analytics = require('analytics');

exports.trackPrinting = {
  init: function () {
    window.print = (function(printfn) {
      return function() {
        analytics.analytics.send('event', 'print');
        printfn();
      };
    })(window.print);
  }
};
