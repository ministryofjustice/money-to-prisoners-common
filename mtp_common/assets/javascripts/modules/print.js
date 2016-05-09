// Print module
/* global exports, require, $ */
'use strict';

var cookie = require('js-cookie');

exports.Print = {
  selector: '.js-Print',

  cookieName: 'remove-print-prompt',

  init: function () {
    this.cacheEls();
    this.bindEvents();
    this.render();
  },

  cacheEls: function () {
    this.$body = $('body');
  },

  bindEvents: function () {
    this.base.Events.on('Print.render', $.proxy(this.render, this));
    this.$body.on('click', this.selector, $.proxy(this.onClickPrint, this));
  },

  render: function () {
    var promptCookie = cookie.get(this.cookieName);

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
      cookie.set(this.cookieName, true);
    }

    // close dialog if open
    this.base.Events.trigger('Dialog.close');

    // trigger a render of this object to check if the cookie is set
    this.base.Events.trigger('Print.render');

    window.print();
  }
};
