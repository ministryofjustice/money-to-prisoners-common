'use strict';

export var Banner = {
  init: function () {
    $('.mtp-banner__title a').each(function () {
      var $control = $(this);
      var $container = $control.closest('.mtp-banner');
      var $body = $container.find('.mtp-banner__body');
      var closed = true;
      $container.attr({
        'aria-expanded': 'false'
      });
      $control.attr({
        'aria-controls': $body.attr('id'),
        'role': 'button'
      });
      $body.attr({
        'role': 'region',
        'aria-hidden': 'true'
      });
      $control.click(function (e) {
        e.preventDefault();
        closed = !closed;
        if (closed) {
          $container.removeClass('mtp-banner--open');
          $container.attr('aria-expanded', 'false');
          $body.attr('aria-hidden', 'true');
        } else {
          $container.addClass('mtp-banner--open');
          $container.attr('aria-expanded', 'true');
          $body.attr('aria-hidden', 'false');
        }
      });
    });
  }
};
