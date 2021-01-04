// YearFieldCompletion module
// Converts a 2-digit year to a full year
'use strict';

export var YearFieldCompletion = {
  selector: '.mtp-date-input__year-completion',

  init: function (selector) {
    $(selector || this.selector).blur(function () {
      var $input = $(this);
      var currentYear = (new Date()).getFullYear();
      var century = 100 * Math.floor(currentYear / 100);
      var eraBoundary = parseInt($input.data('era-boundary'), 10);
      if (isNaN(eraBoundary)) {
        // 2-digit dates are a minimum of 10 years ago by default
        eraBoundary = currentYear - century - 10;
      }
      var value = parseInt($input.val(), 10);
      if (value >= 0 && value <= 99) {
        value = value > eraBoundary ? value + century - 100 : value + century;
        $input.val(value);
      }
    });
  }
};
