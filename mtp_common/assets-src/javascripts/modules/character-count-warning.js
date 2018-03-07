// Show a warning in the form-hint of a field when running out of space
/* globals django */
'use strict';

exports.CharacterCountWarning = {
  init: function () {
    $('.js-character-count').each(function () {
      var $input = $(this);
      var characterLimit = parseInt($input.attr('maxlength'), 10);
      if (!characterLimit) {
        return;
      }
      var $helpElement = $('#' + $input.attr('id') + '-hint');
      if ($helpElement.length !== 1) {
        return;
      }
      var $characterCountWarning = $('<span class="mtp-character-count-hint"></span>');
      $helpElement.append($characterCountWarning);

      function updateCounter() {
        var characterCount = $.trim($input.val()).length;
        var remainingCount = characterLimit - characterCount;
        var message = '';
        if (characterCount > characterLimit) {
          message = django.gettext('Too much text entered');
        } else if(remainingCount <= 25) {
          message = django.interpolate(django.ngettext(
            '%s character remaining',
            '%s characters remaining',
            remainingCount
          ), [remainingCount]);
        }
        $characterCountWarning.text(message)
      }

      updateCounter();
      $input.keyup(updateCounter);
    });
  }
};
