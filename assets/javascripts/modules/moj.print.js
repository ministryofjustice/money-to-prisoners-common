// Print module
// Dependencies: moj, _, jQuery

/* globals Cookies */
(function () {
  'use strict';

  moj.Modules.Print = {
    selector: '.js-Print',

    cookieName: 'remove-print-prompt',

    init: function () {
      _.bindAll(this, 'render', 'onClickPrint');
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
      var promptCookie = Cookies.get(this.cookieName);

      if (promptCookie) {
        var $printTrigger = $('[href="#print-dialog"]');
        var $printDialog = $('#print-dialog');

        $printTrigger
          .removeClass('js-Dialog')
          .addClass('js-Print');

        $printDialog.remove();
      }
    },

    onClickPrint: function (e) {
      var $promptCheck = $('#remove-print-prompt');

      e.preventDefault();

      if ($promptCheck.is(':checked')) {
        Cookies.set(this.cookieName, true);
      }

      // close dialog if open
      moj.Events.trigger('Dialog.close');

      // trigger a render of this object to check if the cookie is set
      moj.Events.trigger('Print.render');

      window.print();
    }
  };

})();
