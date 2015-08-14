// Print module
// Dependencies: moj, _, jQuery

(function () {
  'use strict';

  moj.Modules.Print = {
    selector: '.js-Print',

    init: function () {
      _.bindAll(this, 'render');
      this.cacheEls();
      this.bindEvents();
      this.render();
    },

    cacheEls: function () {
      this.$body = $('body');
    },

    bindEvents: function () {
      moj.Events.on('Print.render', this.render);
      this.$body.on('click', this.selector, this.onClickPrint);
    },

    render: function () {

    },

    onClickPrint: function (e) {
      e.preventDefault();

      window.print();

      // close dialog if open
      moj.Events.trigger('Dialog.close');
    }
  };

})();
