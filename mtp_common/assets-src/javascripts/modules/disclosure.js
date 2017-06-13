// Disclosing box that displays similarly to <details> with isn't supported on older browsers
'use strict';

exports.Disclosure = {
  init: function () {
    $('.mtp-disclosure').each(function () {
      var $control = $(this);
      var $container = $('#' + $control.attr('aria-controls'));
      var currentlyDisclosed = $control.attr('aria-expanded') !== 'true';

      $control.click(function (e) {
        e.preventDefault();
        if (currentlyDisclosed) {
          $container.hide();
          $control.attr('aria-expanded', 'false');
          $control.removeClass('mtp-disclosure--expanded');
        } else {
          $container.show();
          $control.attr('aria-expanded', 'true');
          $control.addClass('mtp-disclosure--expanded');
        }
        currentlyDisclosed = !currentlyDisclosed;
        return false;
      });
      $control.click();
    });
  }
};
