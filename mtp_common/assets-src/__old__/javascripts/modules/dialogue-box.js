// Dialogue box module
'use strict';

exports.DialogueBox = {
  init: function () {
    this.dialogues = [];
    this.$window = $(window);
    $('.mtp-dialogue').each(this.bindDialogues);
    $('.js-dialogue-open').each(this.bindDialogueTriggers);
  },

  bindDialogues: function (i, dialogue) {
    var $dialogue = $(dialogue);
    var $container = $dialogue.parent('.mtp-dialogue__container');

    $dialogue.on('dialogue:open', function () {
      exports.DialogueBox.showingDialogue($dialogue);
      $container.show();
      $dialogue.attr({
        'aria-hidden': 'false',
        'tabindex': '0'
      });
      $dialogue.show();
      $dialogue.trigger('dialogue:reposition');
      $dialogue.focus();
    });

    $dialogue.on('dialogue:close', function () {
      $dialogue.blur();
      $dialogue.hide();
      $dialogue.attr({
        'aria-hidden': 'true'
      });
      $dialogue.removeAttr('tabindex');
      $container.hide();
      exports.DialogueBox.hidingDialogue();
    });

    $dialogue.on('dialogue:reposition', function () {
      var maxHeight = exports.DialogueBox.$window.height() - 200;
      $dialogue.css({
        'marginBottom': '',
        'maxHeight': '',
        'overflowY': ''
      });
      if ($dialogue.outerHeight() >= maxHeight) {
        $dialogue.css({
          'marginBottom': 0,
          'maxHeight': maxHeight + 'px',
          'overflowY': 'scroll'
        });
      }
      $dialogue.css('marginTop', (exports.DialogueBox.$window.height() - $dialogue.outerHeight()) / 2 + 'px');
    });

    $dialogue.on('click', '.js-dialogue-close', function (e) {
      $dialogue.trigger('dialogue:close');
      e.preventDefault();
      return false;
    });

    $dialogue.on('keyup', function (e) {
      if (e.keyCode === 27) {
        $dialogue.trigger('dialogue:close');
        e.preventDefault();
      }
    });
  },

  bindDialogueTriggers: function () {
    var $trigger = $(this);
    var $dialogue = $($trigger.attr('href'));
    if ($dialogue.hasClass('mtp-dialogue')) {
      $trigger.click(function (e) {
        $dialogue.trigger('dialogue:open');
        e.preventDefault();
        return false;
      });
    }
  },

  showingDialogue: function ($dialogue) {
    $.each(exports.DialogueBox.dialogues, function () {
      this.hide();
      this.attr('aria-hidden', 'true');
      this.removeAttr('tabindex');
    });
    exports.DialogueBox.dialogues.push($dialogue);
    if (exports.DialogueBox.dialogues.length === 1) {
      // show backdrop
      var $backdrop = $('<div class="mtp-dialogue__backdrop"></div>');
      $backdrop.hide();
      $('body').prepend($backdrop);
      $backdrop.fadeIn('fast');
      $backdrop.click(function (e) {
        e.preventDefault();
      });

      // monitor window resize
      exports.DialogueBox.$window.on('resize.dialogue', function () {
        $.each(exports.DialogueBox.dialogues, function () {
          this.trigger('dialogue:reposition');
        });
      });
    }
  },

  hidingDialogue: function () {
    exports.DialogueBox.dialogues.pop();
    var dialogueCount = exports.DialogueBox.dialogues.length;
    if (dialogueCount > 0) {
      var $previousDialogue = exports.DialogueBox.dialogues[dialogueCount - 1];
      $previousDialogue.show();
      $previousDialogue.attr({
        'aria-hidden': 'false',
        'tabindex': '0'
      });
      $previousDialogue.trigger('dialogue:reposition');
      $previousDialogue.focus();
    } else if (dialogueCount === 0) {
      // hide backdrop
      var $backdrop = $('.mtp-dialogue__backdrop');
      $backdrop.fadeOut('fast', function () {
        $backdrop.remove();
      });

      // stop monitoring window resize
      exports.DialogueBox.$window.off('resize.dialogue');
    }
  }
};
