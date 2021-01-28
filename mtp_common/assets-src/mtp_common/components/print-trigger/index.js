'use strict';

import Cookie from 'js-cookie';

export var PrintTrigger = {
  triggerSelector: '.mtp-print-trigger',
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
    var $printHidden = $($trigger.data('do-not-print')).not('.govuk-!-display-none-print');
    var $confirmationDialogue = $($trigger.data('confirmation-dialogue'));
    var onClickAction = null;
    if ($confirmationDialogue.length === 1 && $confirmationDialogue.hasClass('mtp-dialogue')) {
      onClickAction = PrintTrigger.makeConfirmationAction($confirmationDialogue, $printHidden);
    } else {
      onClickAction = PrintTrigger.makePrintAction($printHidden);
    }
    $trigger.click(function (e) {
      e.preventDefault();
      onClickAction();
      return false;
    });
  },

  makeConfirmationAction: function ($dialogue, $printHidden) {
    var confirmationCookie = $dialogue.data('confirmation-cookie') || PrintTrigger.confirmationCookie;
    var confirmedCookie = Cookie.get(confirmationCookie);
    var printAction = PrintTrigger.makePrintAction($printHidden);
    if (confirmedCookie) {
      return printAction;
    }

    var $dialoguePrintButton = $dialogue.find(PrintTrigger.triggerSelector);
    $dialoguePrintButton.click(function (e) {
      var $skipConfirmationInput = $dialogue.find('input[name="' + confirmationCookie + '"]');
      if ($skipConfirmationInput.length === 1) {
        if ($skipConfirmationInput.is(':checked')) {
          Cookie.set(confirmationCookie, '1');
        } else {
          Cookie.remove(confirmationCookie);
        }
      }
      $dialogue.trigger('dialogue:close');
      e.preventDefault();
      return false;
    });

    return function () {
      var confirmedCookie = Cookie.get(confirmationCookie);
      if (confirmedCookie) {
        printAction();
      } else {
        $dialogue.trigger('dialogue:open');
      }
    };
  },

  makePrintAction: function ($printHidden) {
    return function () {
      $printHidden.addClass('govuk-!-display-none-print');
      try {
        window.print();
      } catch (e) {}  // eslint-disable-line
      $printHidden.removeClass('govuk-!-display-none-print');
    };
  }
};
