// BeforeUnload module
'use strict';

var analytics = require('./analytics');

exports.Unload = {
  selector: '.js-BeforeUnload',

  init: function () {
    this.cacheEls();
    this.bindEvents();
  },

  cacheEls: function () {
    this.$form = $(this.selector);
    this.initialData = this.$form.serialize();
    this.message = this.$form.data('unload-msg') || '';
    this.submitting = false;
  },

  bindEvents: function () {
    if (this.$form.length > 0) {
      $(window).on('beforeunload', $.proxy(this.beforeUnload, this));
      this.$form.on('click', ':submit', $.proxy(this.formSubmit, this));
    }
  },

  formSubmit: function (e) {
    var $btn = $(e.target);
    var type = $btn.val();

    if (type === 'submit' || type === 'override') {
      this.submitting = true;
    } else {
      this.submitting = false;
    }
  },

  beforeUnload: function () {
    if (this.$form.serialize() !== this.initialData && !this.submitting) {
      analytics.Analytics.send('pageview', '/-leaving_page_dialog/');
      return this.message;
    }
  }
};
