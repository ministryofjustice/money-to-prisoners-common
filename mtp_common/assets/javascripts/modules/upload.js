// UploadSubmit module
/* globals exports */
'use strict';

exports.UploadSubmit = {
  selector: '.upload-form',

  init: function () {
    this.cacheEls();
    this.bindEvents();
    if ($('.message--success').length) {
      this.$formGroups.hide();
      this.$otherFileLink.show();
    }
    this.$uploadFilename.hide();
  },

  cacheEls: function () {
    this.$form = $(this.selector);
    this.$fileChooser = $(this.selector + ' input[type=file]');
    this.$submitButton = $(this.selector + ' input[type=submit]');
    this.$chooseButton = $(this.selector + ' .upload-choose');
    this.$uploadFilename = $(this.selector + ' .upload-filename');
    this.$formGroups = $(this.selector + ' .form-group');
    this.$errorMessages = $(this.selector + ' .error-message, ' + this.selector + ' .error-summary');
    this.$otherFileLink = $(this.selector + ' .upload-otherfilelink');
  },

  bindEvents: function () {
    if (this.$form.length > 0) {
      this.$fileChooser.on('change', $.proxy(this.switchToUpload, this));
    }
  },

  switchToUpload: function() {
    var filePath, filename;
    this.$formGroups.removeClass('error');
    this.$errorMessages.remove();
    filePath = this.$fileChooser.val();
    filename = filePath.replace(/^.*[\\\/]/, '');
    this.$uploadFilename.text(filename).show();
    this.$chooseButton.text('Change file');
  }
};
