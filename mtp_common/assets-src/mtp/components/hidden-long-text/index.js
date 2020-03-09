'use strict';

export var HiddenLongText = {
  init: function () {
    $('.mtp-hidden-long-text').each(function () {
      $(this).click(function (e) {
        e.preventDefault();
        var $link = $(this);
        var textReplacement = $link.data('rest') || '';
        $link.replaceWith(textReplacement);
      });
    });
  }
};
