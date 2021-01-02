// Print module with confirmation dialogue box integration
'use strict';

var cookie = require('js-cookie');

exports.Print = {
  triggerSelector: '.js-print-trigger',
  confirmationCookie: 'remove-print-prompt',

  init: function (triggerSelector) {
    var $triggers = $(triggerSelector || this.triggerSelector);
    if (!window.print) {
      $triggers.hide();
      return;
    }
    $triggers.each(this.bindTriggers);
  },

  bindTriggers: function () {
    var $trigger = $(this);
    var $printHidden = $($trigger.data('do-not-print')).not('.print-hidden');
    var $confirmationDialogue = $($trigger.data('confirmation-dialogue'));
    var onClickAction = null;
    if ($confirmationDialogue.length === 1 && $confirmationDialogue.hasClass('mtp-dialogue')) {
      onClickAction = exports.Print.makeConfirmationAction($confirmationDialogue, $printHidden);
    } else {
      onClickAction = exports.Print.makePrintAction($printHidden);
    }
    $trigger.click(function (e) {
      e.preventDefault();
      onClickAction();
      return false;
    });
  },

  makeConfirmationAction: function ($dialogue, $printHidden) {
    var confirmationCookie = $dialogue.data('confirmation-cookie') || exports.Print.confirmationCookie;
    var confirmedCookie = cookie.get(confirmationCookie);
    var printAction = exports.Print.makePrintAction($printHidden);
    if (confirmedCookie) {
      return printAction;
    }

    var $dialoguePrintButton = $dialogue.find(exports.Print.triggerSelector);
    $dialoguePrintButton.click(function (e) {
      var $skipConfirmationInput = $dialogue.find('input[name="' + confirmationCookie + '"]');
      if ($skipConfirmationInput.length === 1) {
        if ($skipConfirmationInput.is(':checked')) {
          cookie.set(confirmationCookie, '1');
        } else {
          cookie.remove(confirmationCookie);
        }
      }
      $dialogue.trigger('dialogue:close');
      e.preventDefault();
      return false;
    });

    return function () {
      var confirmedCookie = cookie.get(confirmationCookie);
      if (confirmedCookie) {
        printAction();
      } else {
        $dialogue.trigger('dialogue:open');
      }
    };
  },

  makePrintAction: function ($printHidden) {
    return function () {
      $printHidden.addClass('print-hidden');
      try {
        window.print();
      } catch (e) {}  // eslint-disable-line
      $printHidden.removeClass('print-hidden');
    };
  }
};
