// Styled file upload control
'use strict';

export var Upload = {
  selector: '.mtp-upload',

  init: function () {
    $(this.selector).each(function () {
      var $fileChooser = $(this);
      var $chooseButton = $('label[for="' + $fileChooser.attr('id') + '"]');
      if ($chooseButton.length !== 1) {
        return;
      }
      var $uploadFilename = $('<span class="govuk-label mtp-label--upload-filename"></span>');
      $uploadFilename.hide();
      $chooseButton.before($uploadFilename);
      $fileChooser.addClass('mtp-upload--visually-hidden');
      $fileChooser.on('change', function () {
        var filePath = $fileChooser.val();
        var filename = filePath.replace(/^.*[/\\]/, '');
        if (filename.length === 0) {
          $uploadFilename.hide();
          $chooseButton.text(django.gettext('Choose file'));
        } else {
          $uploadFilename.text(filename).show();
          $chooseButton.text(django.gettext('Change file'));
        }
      });
    });
  }
};
