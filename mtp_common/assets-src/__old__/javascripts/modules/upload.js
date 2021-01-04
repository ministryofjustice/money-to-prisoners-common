// UploadSubmit module
'use strict';

exports.Upload = {
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
    this.$chooseButton = $(this.selector + ' .upload-choose');
    this.$uploadFilename = $(this.selector + ' .upload-filename');
    this.$formGroups = $(this.selector + ' .govuk-form-group');
    this.$errorMessages = $(this.selector + ' .govuk-error-message, ' + this.selector + ' .govuk-error-summary');
    this.$otherFileLink = $(this.selector + ' .upload-otherfilelink');
  },

  bindEvents: function () {
    if (this.$form.length > 0) {
      this.$fileChooser.on('change', $.proxy(this.switchToUpload, this));
    }
  },

  switchToUpload: function () {
    var filePath = this.$fileChooser.val();
    var filename = filePath.replace(/^.*[\\\/]/, '');
    this.$formGroups.removeClass('govuk-form-group--error');
    this.$errorMessages.remove();
    this.$uploadFilename.text(filename).show();
    this.$chooseButton.text(django.gettext('Change file'));
  }
};
