// Hides a long piece of text behind a "more..." link
'use strict';

exports.HideLongText = {
  init: function () {
    $('.js-long-text').each(function () {
      $(this).click(function (e) {
        e.preventDefault();
        var $link = $(this);
        var textReplacement = $link.data('rest') || '';
        $link.replaceWith(textReplacement);
      });
    });
  }
};
