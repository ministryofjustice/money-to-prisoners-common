// Focus on search input field
'use strict';

var analytics = require('./analytics');

exports.TrackPrinting = {
  init: function () {
    window.print = (function (printfn) {
      return function () {
        analytics.Analytics.send('event', 'print');
        printfn();
      };
    }(window.print));
  }
};
