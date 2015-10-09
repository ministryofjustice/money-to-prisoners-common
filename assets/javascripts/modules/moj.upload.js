// UploadSubmit module
// Dependencies: moj, _, jQuery
/* globals moj, _, $ */

(function () {
  'use strict';

  moj.Modules.UploadSubmit = {
    selector: '.js-uploadSubmit',

    init: function () {
      _.bindAll(this, 'uploadSubmit');
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

})();
