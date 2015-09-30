// (IE) Polyfills module
// Dependencies: moj, jQuery, poly-checked

(function () {
  'use strict';

  moj.Modules.Polyfills = {
    init: function () {
      this.bindEvents();
      this.render();
    },

    bindEvents: function () {
      moj.Events.on('Polyfills.render', this.render);
    },

    render: function () {
      // :checked selector polyfill for IE 7/8
      $('input:radio, input:checkbox').checkedPolyfill();
    }
  };

})();
