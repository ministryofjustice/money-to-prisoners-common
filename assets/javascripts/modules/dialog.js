// Dialog module
/* global exports, require, $, ga */

'use strict';

var Mojular = require('mojular');
var bindAll = require('lodash/function/bindAll');

exports.Dialog = {
  selector: '.js-Dialog',

  init: function () {
    bindAll(this, 'render', 'openDialog', 'closeDialog', 'onKeyUp');
    this.cacheEls();
    this.bindEvents();
  },

  cacheEls: function () {
    this.$body = $('body');
    this.$backdrop = $('<div>').addClass('Dialog-backdrop');
  },

  bindEvents: function () {
    this.base.Events.on('Dialog.render', this.render);
    this.base.Events.on('Dialog.close', this.closeDialog);
    this.$body.on('click', this.selector, this.render);
    this.$body.on('click', '.js-Dialog-close', this.closeDialog);
  },

  render: function (e) {
    var $triggerEl = $(e.target);
    var target = e.targetSelector || $triggerEl.attr('href');

    e.preventDefault();

    this.$triggerEl = $triggerEl;
    this.openDialog(target);

    // Tell google analytics about the dalog opening
    ga && ga('send', 'event', 'dialog', 'open', target);
  },

  openDialog: function (target) {
    var $dialog = $(typeof target === 'string' ? target : target.dialogTarget);
    var hideClose = $dialog.data('hide-close');
    var disableBackdropClose = $dialog.data('disable-backdrop-close');
    var closeSelector = '.Dialog-close';

    // log warning if target doesn't exist
    if ($dialog.length === 0) {
      Mojular.log('Modules.Dialog Warning: The target element, ' + target + ', does not exist.');
      return;
    }

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
    this.$body.on('click.Dialog', closeSelector, this.closeDialog);
    this.$body.on('keyup.Dialog', this.onKeyUp);

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
    var $dialog = this.$body.find('dialog[open]');
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

    // Tell google analytics about the dalog closing
    ga && ga('send', 'event', 'dialog', 'close');
  },

  onKeyUp: function (e) {
    e = e || window.event;

    if (e.keyCode === 27) {
      this.closeDialog();
    }
  }
};
