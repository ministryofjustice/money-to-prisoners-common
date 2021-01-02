// Disclosing box that displays similarly to <details> with isn't supported on older browsers
'use strict';

exports.Disclosure = {
  init: function () {
    $('.mtp-disclosure').each(function () {
      var $control = $(this);
      var containerID = $control.attr('aria-controls');
      $control.attr('aria-flowto', containerID);
      var $container = $('#' + containerID);
      var currentlyDisclosed = $control.attr('aria-expanded') !== 'true';

      $control.click(function (e) {
        e.preventDefault();
        if (currentlyDisclosed) {
          $container.attr('aria-hidden', 'true');
          $container.hide();
          $control.attr('aria-expanded', 'false');
          $control.attr('aria-selected', 'false');
          $control.removeClass('mtp-disclosure--expanded');
        } else {
          $container.attr('aria-hidden', 'false');
          $container.show();
          $container.focus();
          $control.attr('aria-expanded', 'true');
          $control.attr('aria-selected', 'true');
          $control.addClass('mtp-disclosure--expanded');
        }
        currentlyDisclosed = !currentlyDisclosed;
        return false;
      });
      $control.click();
    });
  }
};
