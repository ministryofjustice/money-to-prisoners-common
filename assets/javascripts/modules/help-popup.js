// Help popup module
/* globals exports, $ */
'use strict';

exports.HelpPopup = {

  init: function () {
    var $helpBoxes = $('.help-box');
    var $helpTitles = $('.help-box-title');
    if ($helpBoxes.length) {
      $helpBoxes.addClass('help-box-hidden');
      $helpTitles
        .attr('aria-expanded', 'false')
        .on('click', this.toggle);
    }
  },

  toggle: function(event) {
    var $helpTitle = $(event.target).parent('.help-box-title');
    var $helpBox = $(event.target).closest('div.help-box');
    var $contents = $helpBox.find('.help-box-contents');
    event.preventDefault();
    $contents.toggle();
    $helpBox.toggleClass('help-box-hidden');
    $helpTitle.attr(
      'aria-expanded',
      $helpTitle.attr('aria-expanded') === 'true' ? 'false' : 'true');
    return false;
  }
};
