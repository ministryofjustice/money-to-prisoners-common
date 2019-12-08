// Focus on search input field
'use strict';

import {Analytics} from './analytics';

export var TrackPrinting = {
  init: function () {
    window.print = (function (printfn) {
      return function () {
        Analytics.send('event', 'print');
        printfn();
      };
    }(window.print));
  }
};
