// Tracks page printing
'use strict';

import {Analytics} from '../analytics';

export var PrintAnalytics = {
  init: function () {
    if (window.print === undefined) {
      return;
    }
    window.print = (function (printfn) {
      return function () {
        Analytics.ga4SendEvent('print');
        printfn();
      };
    }(window.print));
  }
};
