// Dialog module
'use strict';

exports.Dialog = {
  selector: '.js-Dialog',

  init: function () {
    this.cacheEls();
    this.bindEvents();
  },

  cacheEls: function () {
    this.$body = $('body');
    this.$backdrop = $('<div>').addClass('Dialog-backdrop');
  },

  bindEvents: function () {
    this.$body
      .on('Dialog.render', $.proxy(this.render, this))
      .on('Dialog.close', $.proxy(this.closeDialog, this))
      .on('click', this.selector, $.proxy(this.render, this))
      .on('click', '.js-Dialog-close', $.proxy(this.closeDialog, this));
  },

  render: function (e) {
    var $triggerEl = $(e.target);
    var target = e.targetSelector || $triggerEl.attr('href');

    e.preventDefault();

    this.$triggerEl = $triggerEl;
    this.openDialog(target);
  },

  openDialog: function (target) {
    var $dialog = $(typeof target === 'string' ? target : target.dialogTarget);
    var hideClose = $dialog.data('hide-close');
    var disableBackdropClose = $dialog.data('disable-backdrop-close');
    var closeSelector = '.Dialog-close';

    // if close button not needed, don't run
    if (!hideClose) {
      var $close = $('<a>')
        .attr('href', '#')
        .attr('role', 'button')
        .addClass('Dialog-close');

      if ($dialog.data('close-label')) {
        $close.text($dialog.data('close-label'));
      } else {
        $close.text('close');
      }

      $dialog.append($close);
    }

    if (!disableBackdropClose) {
      closeSelector += ', .Dialog-backdrop';
    }

    // bind close events
    this.$body.on('click.Dialog', closeSelector, $.proxy(this.closeDialog, this));
    this.$body.on('keyup.Dialog', $.proxy(this.onKeyUp, this));

    // show dialog and backdrop
    $dialog
      .attr({
        'open': 'true',
        'tabindex': '-1',
        'role': 'dialog'
      })
      .show()
      .focus();

    this.$body.prepend(this.$backdrop);
    $(window).scrollTop(0);
  },

  closeDialog: function (e) {
    var $dialog = this.$body.find('div.Dialog[open]');
    var $close = $dialog.find('.Dialog-close');

    if (e) {
      e.preventDefault();
    }

    if ($dialog.length === 0) {
      return;
    }
    $dialog
      .removeAttr('open tabindex role')
      .hide();

    $close.remove();
    this.$backdrop.remove();

    this.$triggerEl.focus();

    // unbind close events
    this.$body.off('.Dialog');
  },

  onKeyUp: function (e) {
    e = e || window.event;

    if (e.keyCode === 27) {
      this.closeDialog();
    }
  }
};
