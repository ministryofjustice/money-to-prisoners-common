// UploadSubmit module
/* globals exports, require */
'use strict';

var bindAll = require('lodash/function/bindAll');

exports.UploadSubmit = {
  selector: '.js-uploadSubmit',

  init: function () {
    bindAll(this, 'uploadSubmit');
    this.cacheEls();
    this.bindEvents();
  },

  cacheEls: function () {
    this.$form = $(this.selector);
    this.$submitButton = $(this.selector + ' input[type=submit]');
  },

  bindEvents: function () {
    if (this.$form.length > 0) {
      this.$form.on('submit', this.uploadSubmit);
    }
  },

  uploadSubmit: function () {
    var tmpButtonLabel = this.$submitButton.data('value-uploading');
    this.$submitButton
      .addClass('button-secondary')
      .attr('value', tmpButtonLabel);
    this.$submitButton.after('<div class="spinner"></div>');
  }
};
