// Element focus module - allows passing a GET parameter to focus directly on an element on page load
'use strict';

export var ElementFocus = {
  init: function () {
    var query = /(?:\?|^|&)focus=([0-9A-Za-z_-]+)(?:$|&)/.exec(window.location.search);

    if (query && query.length > 1) {
      var elementID = query[1];
      $('#' + elementID).focus();
    }
  }
};
