// Header navigation links
/* global exports, $ */
'use strict';

exports.PropositionHeader = {
  selector: '.header-proposition .js-mtp-header-toggle',

  init: function () {
    var $button = $(this.selector);
    var $linkList = $($button.attr('href'));
    if($linkList.size() === 1) {
      $button.click(function(e) {
        e.preventDefault();
        $button.toggleClass('js-mtp-header-open');
        $linkList.toggleClass('js-visible');
      });
    } else {
      $button.remove();
    }
  }
};
