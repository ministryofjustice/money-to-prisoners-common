// Placeholder attribute polyfill
'use strict';

exports.PlaceholderPolyfill = {
  init: function () {
    if (!('placeholder' in document.createElement('input'))) {
      $('input[placeholder]').each(this.bind);
    }
  },

  bind: function () {
    var $input = $(this);
    var placeholder = $input.attr('placeholder');
    var activeClassName = 'mtp-placeholder-text-active';

    function activate () {
      if ($.trim($input.val()).length < 1) {
        $input.val(placeholder);
        $input.addClass(activeClassName);
      } else {
        $input.removeClass(activeClassName);
      }
    }

    function deactivate () {
      $input.removeClass(activeClassName);
      if ($.trim($input.val()) === placeholder) {
        $input.val('');
      }
    }

    if (placeholder && placeholder.length) {
      activate();
      $input.focus(deactivate).blur(activate);
    }
  }
};
