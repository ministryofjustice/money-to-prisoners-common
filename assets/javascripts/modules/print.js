// Print module
/* global exports, require */
'use strict';

var bindAll = require('lodash/function/bindAll');
var cookie = require('mojular-govuk-elements/modules/cookie-message').Cookie;

exports.Print = {
  selector: '.js-Print',

  cookieName: 'remove-print-prompt',

  init: function () {
    bindAll(this, 'render', 'onClickPrint');
    this.cacheEls();
    this.bindEvents();
    this.render();
  },

  cacheEls: function () {
    this.$body = $('body');
  },

  bindEvents: function () {
    this.base.Events.on('Print.render', this.render);
    this.$body.on('click', this.selector, this.onClickPrint);
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
