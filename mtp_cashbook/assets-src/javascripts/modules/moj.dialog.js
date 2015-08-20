// Dialog module
// Dependencies: moj, _, jQuery

/* globals console */
(function () {
  'use strict';

  moj.Modules.Dialog = {
    selector: '.js-Dialog',

    init: function () {
      _.bindAll(this, 'render', 'closeDialog', 'onKeyUp');
      this.cacheEls();
      this.bindEvents();
    },

    cacheEls: function () {
      this.$body = $('body');
      this.$backdrop = $('<div>').addClass('Dialog-backdrop');
      this.$close = $('<a>');

      // close element
      this.$close
        .attr('href', '#')
        .attr('role', 'button')
        .addClass('Dialog-close');
    },

    bindEvents: function () {
      moj.Events.on('Dialog.render', this.render);
      moj.Events.on('Dialog.close', this.closeDialog);
      this.$body.on('click', this.selector, this.render);
    },

    render: function (e) {
      this.$triggerEl = $(e.target);

      e.preventDefault();
      this.openDialog(this.$triggerEl.attr('href'));
    },

    openDialog: function (target) {
      var $dialog = $(target);

      // log warning if target doesn't exist
      if ($dialog.length === 0) {
        moj.log('Modules.Dialog Warning: The target element, ' + target + ', does not exist.');
        return;
      }

      if ($dialog.data('close-label')) {
        this.$close.text($dialog.data('close-label'));
      } else {
        this.$close.text('close');
      }

      $dialog
        .attr({
          'open': 'true',
          'tabindex': '-1',
          'role': 'dialog'
        })
        .append(this.$close)
        .show()
        .focus();

      this.$body.prepend(this.$backdrop);

      $(window).scrollTop(0);

      // bind close events
      this.$body.on('click.Dialog', '.Dialog-close, .Dialog-backdrop', this.closeDialog);
      this.$body.on('keyup.Dialog', this.onKeyUp);
    },

    closeDialog: function (e) {
      var $dialog = this.$body.find('.Dialog:visible');

      if (e) {
        e.preventDefault();
      }

      if ($dialog.length === 0) {
        return;
      }

      $dialog
        .removeAttr('open tabindex role')
        .hide();

      this.$close.remove();
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

})();
