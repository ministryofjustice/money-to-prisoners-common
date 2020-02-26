// Notifications module
'use strict';

export var Notifications = {
  init: function () {
    $('a.mtp-notification__headline').each(function () {
      var $control = $(this);
      var $container = $control.closest('.mtp-notification');
      var messageID = $container.find('.mtp-notification__message').attr('id');
      if (!messageID) {
        return;
      }
      var closed = true;
      $container.attr('aria-expanded', 'false');
      $control.attr({
        'aria-controls': messageID,
        'aria-flowto': messageID
      });
      $control.click(function (e) {
        e.preventDefault();
        closed = !closed;
        if (closed) {
          $container.removeClass('mtp-notification--open');
          $container.attr('aria-expanded', 'false');
        } else {
          $container.addClass('mtp-notification--open');
          $container.attr('aria-expanded', 'true');
        }
      });
    });
  }
};
