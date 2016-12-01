// Header navigation links
'use strict';

exports.PropositionHeader = {
  selector: '.header-proposition .js-mtp-header-toggle',

  init: function () {
    var $button = $(this.selector);
    var $linkList = $($button.attr('href'));
    if ($linkList.length === 1) {
      $button.click(function (e) {
        e.preventDefault();
        $button.toggleClass('js-mtp-header-open');
        $linkList.toggleClass('js-visible');
      });
    } else {
      $button.remove();
    }
  }
};
